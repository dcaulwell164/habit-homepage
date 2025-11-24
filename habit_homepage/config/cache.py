"""
Cache configuration and utilities for the application.

Provides Redis-based caching with fallback to in-memory caching
for development and testing environments.
"""

import functools
import json
from typing import Any, Callable, TypeVar

import redis
from redis.exceptions import ConnectionError as RedisConnectionError

from habit_homepage.config.logging import get_logger
from habit_homepage.config.settings import settings

logger = get_logger(__name__)

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])


class CacheClient:
    """
    Redis cache client with fallback to in-memory caching.

    Automatically falls back to in-memory caching if Redis is unavailable,
    allowing development without requiring Redis to be running.
    """

    def __init__(self, redis_url: str | None = None):
        """
        Initialize cache client.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
                      If None, uses in-memory cache only
        """
        self.redis_client: redis.Redis | None = None
        self.use_redis = False
        self._memory_cache: dict[str, Any] = {}

        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Redis cache initialized successfully")
            except (RedisConnectionError, Exception) as e:
                logger.warning(f"Redis unavailable, using in-memory cache: {e}")
                self.redis_client = None

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if self.use_redis and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
                return None
            except Exception as e:
                logger.error(f"Redis get error for key {key}: {e}")
                # Fall back to memory cache
                return self._memory_cache.get(key)
        else:
            return self._memory_cache.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise
        """
        if self.use_redis and self.redis_client:
            try:
                serialized = json.dumps(value)
                if ttl:
                    self.redis_client.setex(key, ttl, serialized)
                else:
                    self.redis_client.set(key, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis set error for key {key}: {e}")
                # Fall back to memory cache
                self._memory_cache[key] = value
                return True
        else:
            self._memory_cache[key] = value
            return True

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if key didn't exist
        """
        if self.use_redis and self.redis_client:
            try:
                return bool(self.redis_client.delete(key))
            except Exception as e:
                logger.error(f"Redis delete error for key {key}: {e}")
                return self._memory_cache.pop(key, None) is not None
        else:
            return self._memory_cache.pop(key, None) is not None

    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "habit:*")

        Returns:
            Number of keys deleted
        """
        if self.use_redis and self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            except Exception as e:
                logger.error(f"Redis clear pattern error for {pattern}: {e}")
                # Clear matching keys from memory cache
                count = 0
                keys_to_delete = [
                    k for k in self._memory_cache.keys() if self._match_pattern(k, pattern)
                ]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    count += 1
                return count
        else:
            # Clear matching keys from memory cache
            count = 0
            keys_to_delete = [
                k for k in self._memory_cache.keys() if self._match_pattern(k, pattern)
            ]
            for key in keys_to_delete:
                del self._memory_cache[key]
                count += 1
            return count

    @staticmethod
    def _match_pattern(key: str, pattern: str) -> bool:
        """Simple pattern matching for memory cache (supports * wildcard)."""
        if "*" not in pattern:
            return key == pattern
        # Convert glob pattern to simple starts/ends check
        if pattern.endswith("*"):
            return key.startswith(pattern[:-1])
        if pattern.startswith("*"):
            return key.endswith(pattern[1:])
        return False


# Global cache instance
_cache_client: CacheClient | None = None


def get_cache_client() -> CacheClient:
    """
    Get the global cache client instance.

    Returns:
        CacheClient instance (singleton)
    """
    global _cache_client
    if _cache_client is None:
        redis_url = settings.redis_url if hasattr(settings, "redis_url") else None
        _cache_client = CacheClient(redis_url)
    return _cache_client


def cache(ttl: int = 3600, key_prefix: str = "") -> Callable[[F], F]:
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds (default: 1 hour)
        key_prefix: Prefix for cache keys (default: function name)

    Returns:
        Decorated function

    Example:
        @cache(ttl=300, key_prefix="github")
        def get_contributions(username: str, date: str) -> int:
            # Expensive API call...
            return contributions
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build cache key from function name and arguments
            prefix = key_prefix or func.__name__
            # Create a deterministic key from args and kwargs
            key_parts = [str(arg) for arg in args] + [
                f"{k}={v}" for k, v in sorted(kwargs.items())
            ]
            cache_key = f"{prefix}:{':'.join(key_parts)}"

            # Try to get from cache
            client = get_cache_client()
            cached_value = client.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value

            # Call function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)

            # Only cache non-None results
            if result is not None:
                client.set(cache_key, result, ttl)

            return result

        return wrapper  # type: ignore

    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache keys matching pattern.

    Args:
        pattern: Key pattern (e.g., "habit:*")

    Returns:
        Number of keys deleted

    Example:
        # Invalidate all habit-related cache entries
        invalidate_cache("habit:*")
    """
    client = get_cache_client()
    count = client.clear_pattern(pattern)
    logger.info(f"Invalidated {count} cache keys matching pattern: {pattern}")
    return count
