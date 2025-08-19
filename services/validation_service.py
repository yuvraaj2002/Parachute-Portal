import json
import logging
from typing import Dict, Any, Optional, Tuple
from fastapi import WebSocket, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, UTC

from models.database_models import User
from config import settings

logger = logging.getLogger(__name__)

class ValidationService:
    """Service class for handling all validation logic"""
    
    @staticmethod
    async def validate_websocket_connection(
        websocket: WebSocket, 
        db: Session,
        token: Optional[str] = None
    ) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Validate WebSocket connection and return validation result
        
        Args:
            websocket: WebSocket connection
            db: Database session
            token: JWT token from query parameter or header
        
        Returns:
            Tuple[bool, Optional[User], Optional[str]]: 
                - success: bool
                - user: User object if successful, None otherwise
                - error_reason: error message if failed, None otherwise
        """
        try:
            # Try to get token from query parameter first, then header
            if not token:
                # Check for authorization header
                auth_header = websocket.headers.get("authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
            
            if not token:
                return False, None, "JWT token required (pass as 'token' query parameter or Authorization header)"
            
            # Validate JWT token
            try:
                payload = jwt.decode(
                    token, 
                    settings.jwt_secret_key, 
                    algorithms=[settings.jwt_algorithm]
                )
                user_email = payload.get("sub")
                if not user_email:
                    return False, None, "Invalid token payload"
                    
                # Get user from database
                user = db.query(User).filter(User.email == user_email).first()
                if not user:
                    return False, None, "User not found"
                    
                if not user.is_active:
                    return False, None, "User account inactive"
                    
                return True, user, None
                
            except JWTError:
                return False, None, "Invalid JWT token"
            except Exception as e:
                logger.error(f"Token validation error: {e}")
                return False, None, "Token validation failed"
                
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False, None, f"Validation failed: {str(e)}"
    
    @staticmethod
    def validate_message_format(message: str) -> Tuple[bool, Optional[str]]:
        """
        Validate message format
        
        Returns:
            Tuple[bool, Optional[str]]: 
                - valid: bool
                - error_message: error message if invalid, None otherwise
        """
        if not message or not message.strip():
            return False, "Message cannot be empty"
        
        if len(message.strip()) > 1000:  # Max message length
            return False, "Message too long (max 1000 characters)"
        
        return True, None
    
    @staticmethod
    def validate_chat_id(chat_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate chat ID format

        Returns:
            Tuple[bool, Optional[str]]: 
                - valid: bool
                - error_message: error message if invalid, None otherwise
        """
        if not chat_id or not chat_id.strip():
            return False, "Chat ID cannot be empty"

        if len(chat_id.strip()) > 100:  # Max chat ID length
            return False, "Chat ID too long (max 100 characters)"

        # Ensure chat_id splits into exactly 3 parts by '_'
        parts = chat_id.strip().split('_')
        if len(parts) != 3:
            return False, "Chat ID must have exactly 3 parts separated by underscores (e.g., userId_checkinId_type)"

        return True, None
    
    @staticmethod
    def validate_user_permissions(user: User, required_permission: str = "basic") -> Tuple[bool, Optional[str]]:
        """
        Validate user permissions for specific actions
        
        Returns:
            Tuple[bool, Optional[str]]: 
                - has_permission: bool
                - error_message: error message if no permission, None otherwise
        """
        if required_permission == "admin" and not user.is_admin:
            return False, "Admin permission required"
        
        if required_permission == "provider" and not (user.is_admin or getattr(user, 'is_provider', False)):
            return False, "Provider or admin permission required"
        
        return True, None
    
    @staticmethod
    def create_error_response(error_type: str, message: str, **kwargs) -> Dict[str, Any]:
        """Create standardized error response"""
        error_data = {
            "type": error_type,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
            **kwargs
        }
        return error_data
    
    @staticmethod
    def create_success_response(response_type: str, message: str, **kwargs) -> Dict[str, Any]:
        """Create standardized success response"""
        success_data = {
            "type": response_type,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
            **kwargs
        }
        return success_data
    

    @staticmethod
    def dict_to_string(data):
        """Convert checkin context to readable string format"""
        if not data:
            return "No data available"
        return ", ".join([f"{key}: {value}" for key, value in data.items()])
