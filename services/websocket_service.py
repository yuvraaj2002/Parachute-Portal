import json
import logging
from typing import Dict, Any, Optional, List
from fastapi import WebSocket, WebSocketDisconnect, status
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

class WebSocketService:
    """Service class for managing WebSocket connections and messages"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, user_info: Optional[Dict[str, Any]] = None):
        """Store WebSocket connection and user information (connection already accepted)"""
        self.active_connections[user_id] = websocket
        
        # Store connection metadata
        self.connection_metadata[user_id] = {
            "connected_at": datetime.now(UTC).isoformat(),
            "user_info": user_info or {},
            "last_activity": datetime.now(UTC).isoformat(),
            "message_count": 0
        }
        
        logger.info(f"User {user_id} connected to WebSocket")
        return True
    
    def disconnect(self, user_id: str):
        """Remove user connection and metadata"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")
        
        if user_id in self.connection_metadata:
            del self.connection_metadata[user_id]
    
    async def send_personal_message(self, message: str, user_id: str) -> bool:
        """Send message to a specific user"""
        if user_id not in self.active_connections:
            logger.warning(f"User {user_id} is not connected")
            return False
        
        try:
            await self.active_connections[user_id].send_text(message)
            self._update_activity(user_id)
            return True
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            self.disconnect(user_id)
            return False
    
    async def send_json_message(self, message_data: Dict[str, Any], user_id: str) -> bool:
        """Send JSON message to a specific user"""
        try:
            message_json = json.dumps(message_data)
            return await self.send_personal_message(message_json, user_id)
        except Exception as e:
            logger.error(f"Error sending JSON message to user {user_id}: {e}")
            return False
    
    async def broadcast(self, message: str, exclude_user: Optional[str] = None) -> int:
        """Broadcast message to all connected users"""
        sent_count = 0
        for user_id in list(self.active_connections.keys()):
            if user_id != exclude_user:
                if await self.send_personal_message(message, user_id):
                    sent_count += 1
        return sent_count
    
    async def broadcast_json(self, message_data: Dict[str, Any], exclude_user: Optional[str] = None) -> int:
        """Broadcast JSON message to all connected users"""
        try:
            message_json = json.dumps(message_data)
            return await self.broadcast(message_json, exclude_user)
        except Exception as e:
            logger.error(f"Error broadcasting JSON message: {e}")
            return 0
    
    def is_connected(self, user_id: str) -> bool:
        """Check if user is currently connected"""
        return user_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_connection_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information for a specific user"""
        return self.connection_metadata.get(user_id)
    
    def get_all_connection_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all active connections"""
        return self.connection_metadata.copy()
    
    def _update_activity(self, user_id: str):
        """Update last activity timestamp and message count for a user"""
        if user_id in self.connection_metadata:
            self.connection_metadata[user_id]["last_activity"] = datetime.now(UTC).isoformat()
            self.connection_metadata[user_id]["message_count"] += 1
    
    async def send_welcome_message(self, user_id: str, user_name: str = "User") -> bool:
        """Send welcome message to newly connected user"""
        welcome_message = {
            "type": "connection",
            "message": f"Welcome {user_name}! You are now connected to the Mental Health Bot.",
            "user_id": user_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "connected"
        }
        return await self.send_json_message(welcome_message, user_id)
    
    async def send_error_message(self, user_id: str, error_message: str, error_type: str = "error") -> bool:
        """Send error message to user"""
        error_data = {
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now(UTC).isoformat()
        }
        return await self.send_json_message(error_data, user_id)
    
    async def send_typing_indicator(self, user_id: str, is_typing: bool = True) -> bool:
        """Send typing indicator to user"""
        typing_data = {
            "type": "typing",
            "is_typing": is_typing,
            "timestamp": datetime.now(UTC).isoformat()
        }
        return await self.send_json_message(typing_data, user_id)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get WebSocket service statistics"""
        total_messages = sum(
            metadata.get("message_count", 0) 
            for metadata in self.connection_metadata.values()
        )
        
        return {
            "active_connections": len(self.active_connections),
            "total_messages": total_messages,
            "connected_users": list(self.active_connections.keys()),
            "service_status": "active",
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    async def ping_all_connections(self) -> Dict[str, bool]:
        """Ping all connections to check if they're still alive"""
        ping_results = {}
        for user_id in list(self.active_connections.keys()):
            try:
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.now(UTC).isoformat()
                }
                success = await self.send_json_message(ping_message, user_id)
                ping_results[user_id] = success
                
                if not success:
                    self.disconnect(user_id)
                    
            except Exception as e:
                logger.error(f"Error pinging user {user_id}: {e}")
                ping_results[user_id] = False
                self.disconnect(user_id)
        
        return ping_results
