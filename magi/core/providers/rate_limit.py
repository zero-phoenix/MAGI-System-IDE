import time


class TokenBucket:
    """
    Contención de tasa (Token Bucket) calibrada al 80% de la cuota.
    """
    def __init__(self, rate: float, capacity: float):
        # rate: tokens / second
        # capacity: max tokens in bucket
        self.rate = rate * 0.8 # 20% margin
        self.capacity = capacity * 0.8
        self.tokens = self.capacity
        self.last_update = time.monotonic()

    def consume(self, amount: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_update

        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

class RateLimiterManager:
    def __init__(self):
        self.buckets = {} # provider_id -> TokenBucket

    def get_bucket(self, provider_id: str, rate: float, capacity: float) -> TokenBucket:
        if provider_id not in self.buckets:
            self.buckets[provider_id] = TokenBucket(rate, capacity)
        return self.buckets[provider_id]
