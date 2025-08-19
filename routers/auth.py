import sys
import os
import logging
from datetime import timedelta, datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status
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
    get_current_active_user,
    get_current_admin_user
)
from config import settings
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=SignupResponse)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    When a user tries to register we will look for the current email in the allowed list table.
    If the email is part of allowed list then we will look for the is_registered status.
    In case is_registered status is false we will allow signup, otherwise advise user to login
    """
    # Check if email exists in allowed list
    allowed_email = db.query(AllowedEmail).filter(AllowedEmail.email == user.email).first()
    if not allowed_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not in allowed list"
        )
    
    # Check if email is already registered
    if allowed_email.is_registered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if a user with this email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
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
        
        return {
            "user": db_user,
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except IntegrityError as e:
        db.rollback()
        print(f"IntegrityError: {e}")  # For debugging
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating user"
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error: {e}")  # For debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token using the email
    access_token = create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (client should discard the token)"""
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
    if user_update.username is not None:
        current_user.username = user_update.username
        
    if user_update.email is not None:
        # Check if email is already taken
        if (db.query(User)
            .filter(User.email == user_update.email)
            .filter(User.id != current_user.id)
            .first()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
    
    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating user information"
        )










####################### Future Feature to Reset password ##########################
# @router.post("/forgot-password", response_model=PasswordResetResponse)
# async def forgot_password(
#     request: PasswordResetRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Request a password reset for a user
    
#     This endpoint will:
#     1. Check if the email exists
#     2. Generate a secure reset token
#     3. Send a password reset email with the token
#     4. Return success message (even if email doesn't exist for security)
#     """
#     try:
#         # Determine which base URL to use based on portal boolean
#         base_url = settings.portal_url if request.portal else settings.ohc_url
#         success = password_reset_service.request_password_reset(db, request.email, base_url)
        
#         # Always return success message for security (don't reveal if email exists)
#         return {
#             "message": "If an account with that email exists, a password reset link has been sent.",
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Error in forgot password endpoint: {e}")
#         return {
#             "message": "If an account with that email exists, a password reset link has been sent.",
#             "success": True
#         }

# @router.post("/reset-password", response_model=PasswordResetResponse)
# async def reset_password(
#     request: PasswordResetConfirm,
#     db: Session = Depends(get_db)
# ):
#     """
#     Reset password using a valid reset token
    
#     This endpoint will:
#     1. Validate the reset token
#     2. Check if token is expired or already used
#     3. Update the user's password
#     4. Mark the token as used
#     """
#     try:
#         # Reset password using token
#         success = password_reset_service.reset_password(
#             db, 
#             request.token, 
#             request.new_password
#         )
        
#         if success:
#             return {
#                 "message": "Password reset successfully. You can now log in with your new password.",
#                 "success": True
#             }
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Invalid or expired reset token"
#             )
            
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error in reset password endpoint: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred while resetting your password"
#         )

# @router.get("/validate-reset-token/{token}")
# async def validate_reset_token(
#     token: str,
#     db: Session = Depends(get_db)
# ):
#     """
#     Validate a password reset token
    
#     This endpoint can be used by the frontend to check if a token is valid
#     before showing the password reset form.
#     """
#     try:
#         # Validate token
#         user = password_reset_service.validate_reset_token(db, token)
        
#         if user:
#             return {
#                 "valid": True,
#                 "message": "Token is valid",
#                 "user_email": user.email
#             }
#         else:
#             return {
#                 "valid": False,
#                 "message": "Invalid or expired token"
#             }
            
#     except Exception as e:
#         logger.error(f"Error validating reset token: {e}")
#         return {
#             "valid": False,
#             "message": "Error validating token"
#         } 