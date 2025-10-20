"""Response caching service using Redis."""
import json
import hashlib
from typing import Optional, Dict, Any
import redis
from datetime import timedelta

from src.models.database import get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CacheService:
    """Handle response caching with Redis."""
    
    # Default TTL (time-to-live) in seconds for different model tiers
    DEFAULT_TTL = {
        'tier-1': 86400,  # 24 hours for expensive models (Opus, GPT-4)
        'tier-2': 3600,   # 1 hour for mid-tier models (Sonnet, GPT-4o-mini)
        'tier-3': 1800,   # 30 minutes for cheap models (Haiku, DeepSeek)
    }
    
    def __init__(self):
        """Initialize Redis connection."""
        settings = get_settings()
        self.redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True
        )
        self.enabled = True
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.debug("Redis connection established")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.enabled = False
    
    def _generate_cache_key(
        self,
        messages: list,
        model_id: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a unique cache key for a request.
        
        Uses MD5 hash of messages + model + parameters.
        """
        # Create a string representation of the request
        cache_input = {
            'messages': messages,
            'model': model_id,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        # Convert to JSON and hash
        cache_str = json.dumps(cache_input, sort_keys=True)
        cache_hash = hashlib.md5(cache_str.encode()).hexdigest()
        
        # Prefix with namespace
        return f"llm_cache:{model_id}:{cache_hash}"
    
    def get(
        self,
        messages: list,
        model_id: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if it exists.
        
        Returns:
            Cached response dict or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            cache_key = self._generate_cache_key(messages, model_id, temperature, max_tokens)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache HIT for {model_id}")
                return json.loads(cached_data)
            else:
                logger.debug(f"Cache MISS for {model_id}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        messages: list,
        model_id: str,
        response: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Cache a response.
        
        Args:
            messages: Request messages
            model_id: Model identifier
            response: Response to cache
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            ttl_seconds: Time-to-live in seconds (optional)
        
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            cache_key = self._generate_cache_key(messages, model_id, temperature, max_tokens)
            
            # Use default TTL if not specified
            if ttl_seconds is None:
                ttl_seconds = self.DEFAULT_TTL['tier-2']  # Default to mid-tier
            
            # Store in Redis with expiration
            self.redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(response)
            )
            
            logger.info(f"Cached response for {model_id} (TTL: {ttl_seconds}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def clear_all(self) -> int:
        """
        Clear all cached responses.
        
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys("llm_cache:*")
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {count} cached responses")
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            keys_count = len(self.redis_client.keys("llm_cache:*"))
            
            return {
                "enabled": True,
                "total_keys": keys_count,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": False, "error": str(e)}