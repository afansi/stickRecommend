from functools import wraps
from cachetools import TTLCache
import threading
import time

# Global cache storage: Key -> (TTLCache, Lock)
# We share the same cache and locks across instances to prevent redundant API calls
_global_caches = {}
_cache_creation_lock = threading.Lock()

def ttl_cache(maxsize: int = 100, ttl: int = 300):
    """
    Enhanced decorator to cache function results for `ttl` seconds.
    - Thread-safe (prevents Thundering Herd)
    - Cross-instance (shares cache across different service instances)
    """
    def decorator(func):
        # Unique ID for this function to share cache across service instances
        func_id = f"{func.__module__}.{func.__name__}"
        
        with _cache_creation_lock:
            if func_id not in _global_caches:
                _global_caches[func_id] = {
                    "cache": TTLCache(maxsize=maxsize, ttl=ttl),
                    "locks": {}, # Per-key locks
                    "locks_lock": threading.Lock() # Lock for the locks dict
                }
        
        cache_container = _global_caches[func_id]
        cache = cache_container["cache"]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip 'self' or 'cls' to allow cross-instance sharing of cached data
            # Service methods are usually called as obj.method(*args)
            if args and hasattr(args[0], '__class__'):
                cache_args = args[1:]
            else:
                cache_args = args

            # Convert to hashable types
            hashable_args = tuple(tuple(arg) if isinstance(arg, list) else arg for arg in cache_args)
            key = (hashable_args, tuple(sorted(kwargs.items())))
            
            # FAST PATH: Check if already in cache
            if key in cache:
                return cache[key]
            
            # SLOW PATH: Get or create a lock for this specific key (Thundering Herd Protection)
            with cache_container["locks_lock"]:
                if key not in cache_container["locks"]:
                    cache_container["locks"][key] = threading.Lock()
                key_lock = cache_container["locks"][key]
            
            with key_lock:
                # Double-check cache after acquiring lock
                if key in cache:
                    return cache[key]
                
                # Perform the actual fetch
                result = func(*args, **kwargs)
                cache[key] = result
                
                # Cleanup the key lock to save memory (optional but good practice)
                # Note: We keep it for now for simplicity, as TTLCache handles result eviction
                return result
                
        return wrapper
    return decorator
