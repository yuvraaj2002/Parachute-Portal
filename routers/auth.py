import sys
import os
import logging
from datetime import timedelta, datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any

# Add project root to sys.path for absolute imports
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

from models.database_models import User, AllowedEmail, get_db
from models.pydantic_models.auth_pydantic_models import (UserCreate, UserResponse, UserUpdate, Token, SignupResponse, UserLogin)
from services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_active_user
)
from services.db_service import DatabaseService
from config import settings
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=SignupResponse)
async def signup(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    """
    When a user tries to register we will look for the current email in the allowed list table.
    If the email is part of allowed list then we will look for the is_registered status.
    In case is_registered status is false we will allow signup, otherwise advise user to login
    """
    # Check if email exists in allowed list
    allowed_email = db.query(AllowedEmail).filter(AllowedEmail.email == user.email).first()
    if not allowed_email:
        # Log failed signup attempt
        DatabaseService.create_audit_log(
            db=db,
            user_id=None,
            category="authentication",
            action_details=f"Signup attempt failed for email {user.email} - not in allowed list",
            risk_level="medium",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not in allowed list"
        )
    
    # Check if email is already registered
    if allowed_email.is_registered:
        # Log failed signup attempt
        DatabaseService.create_audit_log(
            db=db,
            user_id=None,
            category="authentication",
            action_details=f"Signup attempt failed for email {user.email} - already registered",
            risk_level="medium",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if a user with this email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        # Log failed signup attempt
        DatabaseService.create_audit_log(
            db=db,
            user_id=None,
            category="authentication",
            action_details=f"Signup attempt failed for email {user.email} - user already exists",
            risk_level="medium",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Creating new user in the Users table with ALL required fields
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )

    try:
        # First add the user to get the ID
        db.add(db_user)
        db.flush() 
        
        # Setting the registered status to True and Linking the user to the allowed email
        allowed_email.is_registered = True  
        allowed_email.user_id = db_user.id  
        allowed_email.updated_at = datetime.now(UTC)
        
        # Now commit both changes
        db.commit()
        db.refresh(db_user)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": db_user.email}
        )
        
        # Log successful signup
        DatabaseService.create_audit_log(
            db=db,
            user_id=db_user.id,
            category="user_management",
            action_details=f"New user {user.email} successfully registered",
            risk_level="low",
            request=request
        )
        
        return {
            "user": db_user,
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except IntegrityError as e:
        db.rollback()
        print(f"IntegrityError: {e}")  # For debugging
        
        # Log failed signup attempt
        DatabaseService.create_audit_log(
            db=db,
            user_id=None,
            category="authentication",
            action_details=f"Signup attempt failed for email {user.email} - integrity error: {str(e)}",
            risk_level="high",
            request=request
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating user"
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error: {e}")  # For debugging
        
        # Log failed signup attempt
        DatabaseService.create_audit_log(
            db=db,
            user_id=None,
            category="authentication",
            action_details=f"Signup attempt failed for email {user.email} - unexpected error: {str(e)}",
            risk_level="high",
            request=request
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        # Log failed login attempt
        DatabaseService.create_audit_log(
            db=db,
            user_id=None,
            category="authentication",
            action_details=f"Failed login attempt for email {credentials.email} - incorrect credentials",
            risk_level="medium",
            request=request
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token using the email
    access_token = create_access_token(
        data={"sub": user.email}
    )
    
    # Log successful login
    DatabaseService.create_audit_log(
        db=db,
        user_id=user.id,
        category="authentication",
        action_details=f"User {user.email} successfully logged in",
        risk_level="low",
        request=request
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout user (client should discard the token)"""
    # Log logout action
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        category="authentication",
        action_details=f"User {current_user.email} logged out",
        risk_level="low",
        request=request
    )
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    # Log user info access
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        category="data_access",
        action_details=f"User {current_user.email} accessed their profile information",
        risk_level="low",
        request=request
    )
    
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_info(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    # Track what fields are being updated
    updated_fields = []
    
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
        updated_fields.append("first_name")
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
        updated_fields.append("last_name")
    if user_update.username is not None:
        current_user.username = user_update.username
        updated_fields.append("username")
        
    if user_update.email is not None:
        # Check if email is already taken
        if (db.query(User)
            .filter(User.email == user_update.email)
            .filter(User.id != current_user.id)
            .first()):
            
            # Log failed update attempt
            DatabaseService.create_audit_log(
                db=db,
                user_id=current_user.id,
                category="user_management",
                action_details=f"User {current_user.email} failed to update email to {user_update.email} - email already taken",
                risk_level="medium",
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
        updated_fields.append("email")
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
        updated_fields.append("password")
    
    try:
        db.commit()
        db.refresh(current_user)
        
        # Log successful update
        if updated_fields:
            DatabaseService.create_audit_log(
                db=db,
                user_id=current_user.id,
                category="user_management",
                action_details=f"User {current_user.email} updated fields: {', '.join(updated_fields)}",
                risk_level="low",
                request=request
            )
        
        return current_user
    except IntegrityError:
        db.rollback()
        
        # Log failed update attempt
        DatabaseService.create_audit_log(
            db=db,
            user_id=current_user.id,
            action="user_update_failed",
            category="user_management",
            action_details=f"User {current_user.email} failed to update profile - integrity error",
            risk_level="high",
            request=request
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating user information"
        )

# New endpoint to get user's audit logs
@router.get("/me/audit-logs")
async def get_user_audit_logs(
    request: Request,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's audit logs"""
    # Log audit log access
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        action="audit_logs_accessed",
        category="data_access",
        action_details=f"User {current_user.email} accessed their audit logs",
        risk_level="low",
        request=request
    )
    
    return DatabaseService.get_user_audit_logs(db, current_user.id, limit)

 