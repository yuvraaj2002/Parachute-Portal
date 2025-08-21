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
    def get_user_audit_logs(
        db: Session,
        user_id: int,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get audit logs for a specific user
        
        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of logs to return
            
        Returns:
            Dictionary containing user's audit logs
        """
        try:
            logs = db.query(AuditLog)\
                .filter(AuditLog.user_id == user_id)\
                .order_by(desc(AuditLog.created_at))\
                .limit(limit)\
                .all()
            
            log_list = []
            for log in logs:
                log_list.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "category": log.category,  # Fixed to use category field
                    "action_details": log.action_details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat()
                })
            
            return {
                "user_id": user_id,
                "logs": log_list,
                "total_count": len(log_list),
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "logs": [],
                "total_count": 0,
                "limit": limit,
                "error": str(e)
            }
    
    @staticmethod
    def get_system_audit_logs(
        db: Session,
        category: Optional[str] = None,  # Changed from action to category
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get system-wide audit logs with optional category filtering
        
        Args:
            db: Database session
            category: Optional filter for specific category type
            limit: Maximum number of logs to return
            
        Returns:
            Dictionary containing system audit logs
        """
        try:
            query = db.query(AuditLog)
            
            if category:
                query = query.filter(AuditLog.category == category)  
            
            logs = query.order_by(desc(AuditLog.created_at)).limit(limit).all()
            
            log_list = []
            for log in logs:
                log_list.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "category": log.category,  # Changed from action to category
                    "action_details": log.action_details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat()
                })
            
            return {
                "category_filter": category,  # Changed from action_filter to category_filter
                "logs": log_list,
                "total_count": len(log_list),
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error retrieving system audit logs: {e}")
            return {
                "category_filter": category,  # Changed from action_filter to category_filter
                "logs": [],
                "total_count": 0,
                "limit": limit,
                "error": str(e)
            }
    
    @staticmethod
    def get_audit_logs_by_date_range(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None,
        category: Optional[str] = None  # Changed from action to category
    ) -> Dict[str, Any]:
        """
        Get audit logs within a specific date range
        
        Args:
            db: Database session
            start_date: Start date for the range
            end_date: End date for the range
            user_id: Optional filter for specific user
            category: Optional filter for specific category
            
        Returns:
            Dictionary containing audit logs in the date range
        """
        try:
            query = db.query(AuditLog)\
                .filter(AuditLog.created_at >= start_date)\
                .filter(AuditLog.created_at <= end_date)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if category:
                query = query.filter(AuditLog.category == category)  # Changed from action to category
            
            logs = query.order_by(desc(AuditLog.created_at)).all()
            
            log_list = []
            for log in logs:
                log_list.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "category": log.category,
                    "action_details": log.action_details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat()
                })
            
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "user_id_filter": user_id,
                "category_filter": category,  # Changed from action_filter to category_filter
                "logs": log_list,
                "total_count": len(log_list)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs by date range: {e}")
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "user_id_filter": user_id,
                "category_filter": category,  # Changed from action_filter to category_filter
                "logs": [],
                "total_count": 0,
                "error": str(e)
            }

    @staticmethod
    def search_audit_logs(
        db: Session,
        search: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Search audit logs with text search and category filtering
        
        Args:
            db: Database session
            search: Optional text to search in action_details, ip_address, or user_agent
            category: Optional filter for specific category
            limit: Maximum number of logs per page
            page: Page number (1-based)
            
        Returns:
            Dictionary containing search results with pagination
        """
        try:
            query = db.query(AuditLog)
            
            # Apply category filter if specified
            if category:
                query = query.filter(AuditLog.category == category)
            
            # Apply text search if specified
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        AuditLog.action_details.ilike(search_term),
                        AuditLog.ip_address.ilike(search_term),
                        AuditLog.user_agent.ilike(search_term)
                    )
                )
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
            
            # Build response
            log_list = []
            for log in logs:
                log_list.append({
                    "id": log.id,
                    "user_id": log.user_id,
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
                "search_term": search,
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
            logger.error(f"Error searching audit logs: {e}")
            return {
                "search_term": search,
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
