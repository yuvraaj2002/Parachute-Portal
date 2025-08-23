import logging
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, date, UTC
from fastapi import Request
from models.database_models import AuditLog, User
from sqlalchemy import or_

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service class for database operations including audit logging"""
    
    @staticmethod
    def create_audit_log(
        db: Session,
        user_id: int,
        category: str,
        action_details: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """
        Create an audit log entry for HIPAA compliance and security tracking
        
        Args:
            db: Database session
            user_id: ID of the user performing the action (can be None for unauthenticated actions)
            category: The specific action performed (e.g., 'user_login', 'user_signup', 'password_change')
            action_details: Additional details about the action
            request: FastAPI request object to extract IP address and user agent
            
        Returns:
            AuditLog object if successful, None if failed
        """
        try:
            # Extract IP address and user agent from request if provided
            if request:
                # Get client IP address
                if request.client:
                    ip_address = request.client.host
                elif "x-forwarded-for" in request.headers:
                    ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()
                elif "x-real-ip" in request.headers:
                    ip_address = request.headers["x-real-ip"]
                
                # Get user agent
                user_agent = request.headers.get("user-agent")
            
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                category=category,  # Use category field
                action_details=action_details,
                table_name=resource_type or "system",  # Use table_name field
                record_id=resource_id,  # Use record_id field
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.info(f"Audit log created: {category} by user {user_id} from IP {ip_address}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Error creating audit log for action {category}: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_all_audit_logs(
        db: Session,
        limit: int = 100,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get all audit logs with pagination
        
        Args:
            db: Database session
            limit: Maximum number of logs per page
            page: Page number (1-based)
            
        Returns:
            Dictionary containing all audit logs with pagination
        """
        try:
            query = db.query(AuditLog)
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
            
            # Build response
            log_list = []
            for log in logs:
                # Get user first name if user_id exists
                user_name = None
                if log.user_id:
                    user = db.query(User).filter(User.id == log.user_id).first()
                    if user:
                        user_name = user.first_name
                
                log_list.append({
                    "id": log.id,
                    "user": user_name,
                    "category": log.category,
                    "action_details": log.action_details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat()
                })
            
            # Calculate pagination info
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "logs": log_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "limit": limit,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving all audit logs: {e}")
            return {
                "logs": [],
                "pagination": {
                    "current_page": page,
                    "total_pages": 0,
                    "total_count": 0,
                    "limit": limit,
                    "has_next": False,
                    "has_prev": False
                },
                "error": str(e)
            }

    @staticmethod
    def get_audit_logs_by_type(
        db: Session,
        category: str,
        limit: int = 100,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get audit logs filtered by type/category with pagination
        
        Args:
            db: Database session
            category: Category/type to filter by
            limit: Maximum number of logs per page
            page: Page number (1-based)
            
        Returns:
            Dictionary containing filtered audit logs with pagination
        """
        try:
            query = db.query(AuditLog).filter(AuditLog.category == category)
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
            
            # Build response
            log_list = []
            for log in logs:
                # Get user first name if user_id exists
                user_name = None
                if log.user_id:
                    user = db.query(User).filter(User.id == log.user_id).first()
                    if user:
                        user_name = user.first_name
                
                log_list.append({
                    "id": log.id,
                    "user": user_name,
                    "category": log.category,
                    "action_details": log.action_details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat()
                })
            
            # Calculate pagination info
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "category_filter": category,
                "logs": log_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "limit": limit,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs by type {category}: {e}")
            return {
                "category_filter": category,
                "logs": [],
                "pagination": {
                    "current_page": page,
                    "total_pages": 0,
                    "total_count": 0,
                    "limit": limit,
                    "has_next": False,
                    "has_prev": False
                },
                "error": str(e)
            }

    @staticmethod
    def get_audit_logs_by_user(
        db: Session,
        user_id: int,
        limit: int = 100,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get audit logs filtered by specific user with pagination
        
        Args:
            db: Database session
            user_id: ID of the user to filter by
            limit: Maximum number of logs per page
            page: Page number (1-based)
            
        Returns:
            Dictionary containing filtered audit logs with pagination
        """
        try:
            query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
            
            # Get user information
            user = db.query(User).filter(User.id == user_id).first()
            user_info = None
            if user:
                user_info = {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username
                }
            
            # Build response
            log_list = []
            for log in logs:
                log_list.append({
                    "id": log.id,
                    "user": user_info,
                    "category": log.category,
                    "action_details": log.action_details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat()
                })
            
            # Calculate pagination info
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "user_filter": user_info,
                "logs": log_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "limit": limit,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs for user {user_id}: {e}")
            return {
                "user_filter": None,
                "logs": [],
                "pagination": {
                    "current_page": page,
                    "total_pages": 0,
                    "total_count": 0,
                    "limit": limit,
                    "has_next": False,
                    "has_prev": False
                },
                "error": str(e)
            }

    @staticmethod
    def get_audit_logs_combined_filter(
        db: Session,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get audit logs with combined filtering (type + user) and pagination
        
        Args:
            db: Database session
            category: Optional category/type filter
            user_id: Optional user ID filter
            limit: Maximum number of logs per page
            page: Page number (1-based)
            
        Returns:
            Dictionary containing filtered audit logs with pagination
        """
        try:
            query = db.query(AuditLog)
            
            # Apply category filter if specified
            if category:
                query = query.filter(AuditLog.category == category)
            
            # Apply user filter if specified
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
            
            # Get user information if user_id filter is applied
            user_info = None
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user_info = {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "username": user.username
                    }
            
            # Build response
            log_list = []
            for log in logs:
                # Get user first name for each log entry
                log_user_name = None
                if log.user_id:
                    user = db.query(User).filter(User.id == log.user_id).first()
                    if user:
                        log_user_name = user.first_name
                
                log_list.append({
                    "id": log.id,
                    "user": log_user_name,
                    "category": log.category,
                    "action_details": log.action_details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat()
                })
            
            # Calculate pagination info
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "filters": {
                    "category": category,
                    "user_id": user_id,
                    "user_info": user_info
                },
                "logs": log_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "limit": limit,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs with combined filters: {e}")
            return {
                "filters": {
                    "category": category,
                    "user_id": user_id,
                    "user_info": None
                },
                "logs": [],
                "pagination": {
                    "current_page": page,
                    "total_pages": 0,
                    "total_count": 0,
                    "limit": limit,
                    "has_next": False,
                    "has_prev": False
                },
                "error": str(e)
            }
