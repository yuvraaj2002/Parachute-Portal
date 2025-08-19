import json
import logging
from typing import Any, Optional
from datetime import timedelta
from services.redis_service import redis_service

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_service = redis_service
        if not self.redis_service.is_connected():
            logger.warning("Redis connection not available. Caching will be disabled.")

    def get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        if not self.redis_service.is_connected():
            return None
        
        try:
            client = self.redis_service.get_client()
            if client is None:
                return None
            data = client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_minutes: int = 10) -> bool:
        """Set cached data with TTL"""
        if not self.redis_service.is_connected():
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            ttl_seconds = ttl_minutes * 60
            client = self.redis_service.get_client()
            if client is None:
                return False
            client.setex(key, ttl_seconds, serialized_value)
            logger.info(f"Cached data for key {key} with TTL {ttl_minutes}m")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete cached data"""
        if not self.redis_service.is_connected():
            return False
        
        try:
            client = self.redis_service.get_client()
            if client is None:
                return False
            client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def clear_analytics_cache(self):
        """Clear all analytics cache keys"""
        if not self.redis_service.is_connected():
            return
        
        try:
            pattern = "analytics:*"
            client = self.redis_service.get_client()
            if client is None:
                return
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
                logger.info(f"Cleared {len(keys)} analytics cache keys")
        except Exception as e:
            logger.error(f"Error clearing analytics cache: {e}")

# Global cache service instance
cache_service = CacheService() 