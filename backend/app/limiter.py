import time
from collections import defaultdict
from fastapi import HTTPException, status

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.clients = defaultdict(list)

    def check(self, key: str):
        now = time.time()
        window = now - 60
        self.clients[key] = [t for t in self.clients[key] if t > window]
        if len(self.clients[key]) >= self.rpm:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait 60 seconds before retrying."
            )
        self.clients[key].append(now)

auth_limiter = RateLimiter(requests_per_minute=10)
job_limiter = RateLimiter(requests_per_minute=5)
general_limiter = RateLimiter(requests_per_minute=120)
