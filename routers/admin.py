import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from models.database_models import User, get_db
from services.auth_service import get_current_admin_user
from services.db_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Administration"])

@router.get("/audit-logs")
async def get_all_audit_logs(
    request: Request,
    limit: int = 100,
    page: int = 1,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all audit logs with pagination (admin only)"""
    # Log admin audit log access
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        category="system_admin",
        action_details=f"Admin {current_user.email} accessed all audit logs with pagination: limit={limit}, page={page}",
        request=request
    )
    
    return DatabaseService.get_all_audit_logs(db, limit, page)

@router.get("/audit-logs/type/{category}")
async def get_audit_logs_by_type(
    category: str,
    request: Request,
    limit: int = 100,
    page: int = 1,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs filtered by type/category (admin only)"""
    # Log admin audit log access by type
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        category="system_admin",
        action_details=f"Admin {current_user.email} accessed audit logs by type '{category}' with pagination: limit={limit}, page={page}",
        request=request
    )
    
    return DatabaseService.get_audit_logs_by_type(db, category, limit, page)

@router.get("/audit-logs/user/{user_id}")
async def get_audit_logs_by_user(
    user_id: int,
    request: Request,
    limit: int = 100,
    page: int = 1,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs filtered by specific user (admin only)"""
    # Log admin audit log access by user
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        category="system_admin",
        action_details=f"Admin {current_user.email} accessed audit logs for user ID {user_id} with pagination: limit={limit}, page={page}",
        request=request
    )
    
    return DatabaseService.get_audit_logs_by_user(db, user_id, limit, page)

@router.get("/audit-logs/filter")
async def get_audit_logs_combined_filter(
    request: Request,
    category: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 100,
    page: int = 1,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with combined filtering (type + user) and pagination (admin only)"""
    # Log admin combined filter access
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        category="system_admin",
        action_details=f"Admin {current_user.email} accessed audit logs with combined filters: category='{category}', user_id={user_id}, limit={limit}, page={page}",
        request=request
    )
    
    return DatabaseService.get_audit_logs_combined_filter(db, category, user_id, limit, page)
