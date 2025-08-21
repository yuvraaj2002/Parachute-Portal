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
async def get_system_audit_logs(
    request: Request,
    category: Optional[str] = None,  
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system-wide audit logs (admin only)"""
    # Log admin audit log access
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        category="system_admin",
        action_details=f"Admin {current_user.email} accessed system audit logs with filters: category={category}, limit={limit}",
        request=request
    )
    
    return DatabaseService.get_system_audit_logs(db, category, limit)  

@router.get("/audit-logs/date-range")
async def get_audit_logs_by_date_range(
    request: Request,
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None,
    category: Optional[str] = None,  
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs within a specific date range (admin only)"""
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
        )
    
    # Log admin date range audit log access
    DatabaseService.create_audit_log(
        db=db,
        user_id=current_user.id,
        category="system_admin",
        action_details=f"Admin {current_user.email} accessed audit logs for date range {start_date} to {end_date}",
        request=request
    )
    
    return DatabaseService.get_audit_logs_by_date_range(db, start_dt, end_dt, user_id, category)  # Changed from action to category
