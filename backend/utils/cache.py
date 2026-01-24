from functools import wraps
from cachetools import TTLCache

# Global cache storage: Key -> TTLCache
# We create a separate cache instance for each decorated function to avoid collisions
_caches = {}

def ttl_cache(maxsize: int = 100, ttl: int = 300):
    """
    Decorator to cache function results for `ttl` seconds.
    maxsize: Max number of items to store.
    ttl: Time to live in seconds.
    """
    def decorator(func):
        # Create a unique cache for this function
        cache = TTLCache(maxsize=maxsize, ttl=ttl)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a simplified key key from args/kwargs
            # Note: This simple key generation might not handle unhashable types perfectly
            # but usually fine for simple string args (tickers).
            key = (args, tuple(sorted(kwargs.items())))
            
            if key in cache:
                return cache[key]
            
            result = func(*args, **kwargs)
            cache[key] = result
            return result
        return wrapper
    return decorator
