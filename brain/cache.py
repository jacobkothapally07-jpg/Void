import time

class QuantumCache:
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl_seconds

    def get(self, query: str):
        key = query.strip().lower()
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["response"]
            else:
                del self.cache[key]
        return None

    def set(self, query: str, response: str):
        key = query.strip().lower()
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest]
        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }

QUANTUM_CACHE = QuantumCache()
