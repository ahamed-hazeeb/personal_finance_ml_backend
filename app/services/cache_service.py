"""
Caching service using Redis for improved performance.

This module provides caching functionality for predictions, health scores,
and other computationally expensive operations.
"""
import json
import hashlib
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import redis

from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import track_cache_hit, track_cache_miss

logger = get_logger(__name__)


class CacheService:
    """
    Redis-based caching service.
    
    Provides methods for caching and retrieving prediction results,
    health scores, and other frequently accessed data.
    """
    
    def __init__(self):
        """Initialize cache service with Redis connection."""
        self.enabled = settings.CACHE_ENABLED
        
        if self.enabled:
            try:
                self.redis_client = redis.from_url(
                    settings.get_redis_url(),
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
                self.enabled = False
                self.redis_client = None
        else:
            self.redis_client = None
            logger.info("Caching is disabled")
    
    def _generate_cache_key(
        self,
        prefix: str,
        user_id: int,
        params: Dict[str, Any]
    ) -> str:
        """
        Generate a cache key from parameters.
        
        Args:
            prefix: Cache key prefix (e.g., 'prediction', 'health_score')
            user_id: User ID
            params: Dictionary of parameters to include in key
            
        Returns:
            Cache key string
        """
        # Sort params for consistent key generation
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:{user_id}:{params_hash}"
    
    def get(
        self,
        cache_type: str,
        user_id: int,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached value.
        
        Args:
            cache_type: Type of cache (e.g., 'prediction', 'health_score')
            user_id: User ID
            params: Optional parameters for cache key generation
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None
        
        try:
            key = self._generate_cache_key(cache_type, user_id, params or {})
            cached_value = self.redis_client.get(key)
            
            if cached_value:
                track_cache_hit(cache_type)
                logger.debug(f"Cache hit: {key}")
                return json.loads(cached_value)
            else:
                track_cache_miss(cache_type)
                logger.debug(f"Cache miss: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        cache_type: str,
        user_id: int,
        value: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set cache value.
        
        Args:
            cache_type: Type of cache (e.g., 'prediction', 'health_score')
            user_id: User ID
            value: Value to cache
            ttl_seconds: Time to live in seconds (None for default)
            params: Optional parameters for cache key generation
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_cache_key(cache_type, user_id, params or {})
            ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
            
            # Add metadata
            cached_data = {
                **value,
                "_cached_at": datetime.utcnow().isoformat(),
                "_expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
            }
            
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(cached_data)
            )
            
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def invalidate(
        self,
        cache_type: str,
        user_id: int,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Invalidate cached value.
        
        Args:
            cache_type: Type of cache
            user_id: User ID
            params: Optional parameters for cache key generation
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_cache_key(cache_type, user_id, params or {})
            self.redis_client.delete(key)
            logger.debug(f"Cache invalidated: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False
    
    def invalidate_user(self, user_id: int) -> bool:
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Find all keys for this user
            pattern = f"*:{user_id}:*"
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            
            logger.info(f"Invalidated {deleted_count} cache entries for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"User cache invalidation error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_keys": self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global cache service instance
_cache_service = None


def get_cache_service() -> CacheService:
    """
    Get the global cache service instance.
    
    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
