import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, List

from models.database_models import User, get_db, AllowedEmail
from models.pydantic_models.admin_pydantic_models import (
    UserListResponse,
    UserDeactivateRequest,
    UserDeactivateResponse,
    UserReactivateRequest,
    UserReactivateResponse,
    AddAllowedEmailRequest,
    AddAllowedEmailResponse
)
from services.auth_service import get_current_admin_user
from services.db_service import DatabaseService
from datetime import UTC


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Administration"])

@router.get("/audit-logs")
async def get_audit_logs(
    request: Request,
    limit: int = 100,
    page: int = 1,
    category: Optional[str] = None,
    user_id: Optional[int] = None,
    date_range: Optional[str] = None,
    user_type: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with comprehensive filtering and pagination (admin only)"""
    # Log admin audit log access
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        category="system_admin",
        action_details=f"Admin {current_user.email} accessed audit logs with filters: category='{category}', user_id={user_id}, date_range='{date_range}', user_type='{user_type}', limit={limit}, page={page}",
        request=request
    )
    
    return DatabaseService.get_audit_logs_enhanced_filter(
        db, category, user_id, date_range, user_type, limit, page
    )

@router.get("/users", response_model=List[UserListResponse])
async def get_all_users(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get list of all non-admin users (admin only)"""
    try:
        # Get all users except admin users
        users = db.query(User).filter(User.is_admin == False).all()
        
        # Log admin action
        DatabaseService.create_audit_log(
            db=db,
            user_id=current_user.id,
            category="system_admin",
            action_details=f"Admin {current_user.email} retrieved list of all non-admin users (count: {len(users)})",
            request=request
        )
        
        return users
        
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )

@router.put("/users/deactivate", response_model=UserDeactivateResponse)
async def deactivate_user(
    request_data: UserDeactivateRequest,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate a user's active status (admin only)"""
    try:
        # Get the user to deactivate
        user = db.query(User).filter(User.id == request_data.user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate admin users"
            )
        
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself"
            )
        
        # Deactivate the user
        user.is_active = False
        user.updated_at = datetime.now(UTC)
        db.commit()
        
        # Log admin action
        DatabaseService.create_audit_log(
            db=db,
            user_id=current_user.id,
            category="system_admin",
            action_details=f"Admin {current_user.email} deactivated user {user.email} (ID: {user.id})",
            request=request
        )
        
        return UserDeactivateResponse(
            message="User deactivated successfully",
            user_id=user.id,
            is_active=user.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deactivating user"
        )

@router.put("/users/reactivate", response_model=UserReactivateResponse)
async def reactivate_user(
    request_data: UserReactivateRequest,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Reactivate a deactivated user (admin only)"""
    try:
        # Get the user to reactivate
        user = db.query(User).filter(User.id == request_data.user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify admin users"
            )
        
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active"
            )
        
        # Reactivate the user
        user.is_active = True
        user.updated_at = datetime.now(UTC)
        db.commit()
        
        # Log admin action
        DatabaseService.create_audit_log(
            db=db,
            user_id=current_user.id,
            category="system_admin",
            action_details=f"Admin {current_user.email} reactivated user {user.email} (ID: {user.id})",
            request=request
        )
        
        return UserReactivateResponse(
            message="User reactivated successfully",
            user_id=user.id,
            is_active=user.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reactivating user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reactivating user"
        )

@router.post("/allowed-emails", response_model=AddAllowedEmailResponse)
async def add_allowed_email(
    request_data: AddAllowedEmailRequest,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Add a new email to the allowed emails table (admin only) - defaults to staff role"""
    try:
        # Check if email already exists
        existing_email = db.query(AllowedEmail).filter(AllowedEmail.email == request_data.email).first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists in allowed emails list"
            )
        
        # Create new allowed email entry - always as staff member
        new_allowed_email = AllowedEmail(
            email=request_data.email,
            role="staff",  # Default role is always staff
            is_registered=False
        )
        
        db.add(new_allowed_email)
        db.commit()
        db.refresh(new_allowed_email)
        
        # Log admin action
        DatabaseService.create_audit_log(
            db=db,
            user_id=current_user.id,
            category="system_admin",
            action_details=f"Admin {current_user.email} added new allowed email: {request_data.email} as staff member",
            request=request
        )
        
        return AddAllowedEmailResponse(
            message="Email added to allowed list successfully as staff member",
            email=new_allowed_email.email,
            role=new_allowed_email.role,
            id=new_allowed_email.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding allowed email: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding allowed email"
        )
