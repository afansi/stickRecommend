import time
import threading
from collections import deque

class RateLimiter:
    """
    Token bucket rate limiter for Yahoo Finance API.
    Limits: ~2000 requests/hour = ~33 requests/minute
    Strategy: Allow 25 requests/minute with 500ms delay between requests
    """
    def __init__(self, max_requests_per_minute=25, delay_between_requests=0.5):
        self.max_requests = max_requests_per_minute
        self.delay = delay_between_requests
        self.requests = deque()
        self.lock = threading.Lock()
        
    def wait_if_needed(self):
        """
        Block if rate limit would be exceeded.
        Implements both:
        1. Request count limit (25/min)
        2. Minimum delay between requests (500ms)
        """
        with self.lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            while self.requests and now - self.requests[0] > 60:
                self.requests.popleft()
            
            # Check if we've hit the limit
            if len(self.requests) >= self.max_requests:
                # Wait until oldest request expires
                sleep_time = 60 - (now - self.requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    now = time.time()
                    # Clean up again
                    while self.requests and now - self.requests[0] > 60:
                        self.requests.popleft()
            
            # Add delay between consecutive requests
            if self.requests:
                time_since_last = now - self.requests[-1]
                if time_since_last < self.delay:
                    time.sleep(self.delay - time_since_last)
                    now = time.time()
            
            # Record this request
            self.requests.append(now)

# Global rate limiter instance
yahoo_rate_limiter = RateLimiter()
