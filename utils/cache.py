"""
Caching utilities for Discord Music Bot
Provides TTL-based caching for expensive operations

FIX BUG #4: Changed 'name' to 'cache_name' in predefined cache configs
"""
import time
import logging
import hashlib
import json
from collections import OrderedDict
from typing import Any, Optional, Callable, TypeVar, Dict
from functools import wraps
import asyncio

logger = logging.getLogger('discord_bot')

T = TypeVar('T')


class TTLCache:
    """
    Time-To-Live cache with automatic expiration
    
    Features:
    - Automatic expiration based on TTL
    - LRU eviction when max size reached
    - Thread-safe operations
    - Hit/miss statistics
    """
    
    def __init__(self, max_size: int = 1000, ttl: float = 300):
        """
        Initialize TTL cache
        
        Args:
            max_size: Maximum number of items to cache
            ttl: Time-to-live in seconds
        """
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._hits = 0
        self._misses = 0
        self._lock = asyncio.Lock()
        
        logger.debug(f"TTLCache initialized: max_size={max_size}, ttl={ttl}s")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                
                # Check if expired
                if time.time() - timestamp < self._ttl:
                    # Move to end (LRU)
                    self._cache.move_to_end(key)
                    self._hits += 1
                    logger.debug(f"Cache hit: {key}")
                    return value
                else:
                    # Expired, remove
                    del self._cache[key]
                    logger.debug(f"Cache expired: {key}")
            
            self._misses += 1
            logger.debug(f"Cache miss: {key}")
            return None
    
    async def set(self, key: str, value: Any) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Cache evicted (LRU): {oldest_key}")
            
            self._cache[key] = (value, time.time())
            self._cache.move_to_end(key)
            logger.debug(f"Cache set: {key}")
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cached values"""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info("Cache cleared")
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items()
                if current_time - timestamp >= self._ttl
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'ttl': self._ttl,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'total_requests': total_requests
        }
    
    def __len__(self) -> int:
        """Get number of cached items"""
        return len(self._cache)
    
    def __repr__(self) -> str:
        """String representation"""
        stats = self.get_stats()
        return f"TTLCache(size={stats['size']}/{stats['max_size']}, hit_rate={stats['hit_rate']})"


class CacheManager:
    """
    Manages multiple named caches with different configurations
    """
    
    def __init__(self):
        self._caches: Dict[str, TTLCache] = {}
        self._lock = asyncio.Lock()
        logger.info("CacheManager initialized")
    
    async def get_cache(
        self, 
        cache_name: str,  # FIX BUG #4: Changed parameter name from 'name' to 'cache_name' for consistency
        max_size: int = 1000, 
        ttl: float = 300
    ) -> TTLCache:
        """
        Get or create a named cache
        
        Args:
            cache_name: Cache name
            max_size: Maximum cache size
            ttl: Time-to-live in seconds
            
        Returns:
            TTLCache instance
        """
        async with self._lock:
            if cache_name not in self._caches:
                self._caches[cache_name] = TTLCache(max_size=max_size, ttl=ttl)
                logger.info(f"Created cache: {cache_name} (max_size={max_size}, ttl={ttl}s)")
            
            return self._caches[cache_name]
    
    async def clear_cache(self, cache_name: str) -> bool:
        """
        Clear a specific cache
        
        Args:
            cache_name: Cache name
            
        Returns:
            True if cache was cleared
        """
        async with self._lock:
            if cache_name in self._caches:
                await self._caches[cache_name].clear()
                return True
            return False
    
    async def clear_all(self) -> None:
        """Clear all caches"""
        async with self._lock:
            for cache in self._caches.values():
                await cache.clear()
            logger.info("All caches cleared")
    
    async def cleanup_all_expired(self) -> int:
        """
        Cleanup expired entries in all caches
        
        Returns:
            Total number of entries removed
        """
        total_removed = 0
        async with self._lock:
            for cache in self._caches.values():
                removed = await cache.cleanup_expired()
                total_removed += removed
        
        if total_removed > 0:
            logger.info(f"Cleaned up {total_removed} expired entries across all caches")
        
        return total_removed
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all caches
        
        Returns:
            Dictionary mapping cache names to their stats
        """
        return {
            name: cache.get_stats()
            for name, cache in self._caches.items()
        }
    
    def list_caches(self) -> list[str]:
        """Get list of all cache names"""
        return list(self._caches.keys())


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Hash-based cache key
    """
    # Create a stable string representation
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = "|".join(key_parts)
    
    # Hash for consistent length
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    cache_name: str = "default",
    ttl: float = 300,
    max_size: int = 1000,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results
    
    Args:
        cache_name: Name of cache to use
        ttl: Time-to-live in seconds
        max_size: Maximum cache size
        key_func: Custom function to generate cache key
        
    Example:
        @cached(cache_name="youtube", ttl=300)
        async def fetch_video_info(url: str):
            # Expensive operation
            return info
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_cache_manager()
            cache = await manager.get_cache(cache_name, max_size=max_size, ttl=ttl)
            
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Use function name and arguments
                key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result)
            
            return result
        
        return wrapper
    return decorator


# FIX BUG #4: Changed 'name' to 'cache_name' in all predefined cache configurations
# This matches the parameter name expected by the @cached() decorator
YOUTUBE_CACHE_CONFIG = {
    'cache_name': 'youtube_metadata',
    'ttl': 300,  # 5 minutes
    'max_size': 500
}

LLM_CACHE_CONFIG = {
    'cache_name': 'llm_responses',
    'ttl': 600,  # 10 minutes
    'max_size': 200
}

SEARCH_CACHE_CONFIG = {
    'cache_name': 'search_results',
    'ttl': 120,  # 2 minutes
    'max_size': 300
}

SYNTHESIS_CACHE_CONFIG = {
    'cache_name': 'synthesized_music',
    'ttl': 3600,  # 1 hour
    'max_size': 50
}


async def initialize_default_caches():
    """Initialize all default caches"""
    manager = get_cache_manager()
    
    configs = [
        YOUTUBE_CACHE_CONFIG,
        LLM_CACHE_CONFIG,
        SEARCH_CACHE_CONFIG,
        SYNTHESIS_CACHE_CONFIG
    ]
    
    for config in configs:
        await manager.get_cache(**config)
    
    logger.info("Default caches initialized")


async def cleanup_task(interval: int = 300):
    """
    Background task to cleanup expired cache entries
    
    Args:
        interval: Cleanup interval in seconds
    """
    manager = get_cache_manager()
    
    while True:
        try:
            await asyncio.sleep(interval)
            removed = await manager.cleanup_all_expired()
            if removed > 0:
                logger.info(f"Cache cleanup: removed {removed} expired entries")
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in cache cleanup task: {e}", exc_info=True)
