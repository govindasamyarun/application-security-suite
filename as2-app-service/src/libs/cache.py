import redis
from flask import current_app

class Cache:
    def __init__(self):
        self.redis = redis.Redis(host=current_app.config["REDIS_HOST"], port=current_app.config["REDIS_PORT"], db=0)

    def write(self, k, v):
        # This function writes the key and value to the cache 
        self.redis.set(k, v)

    def read(self, k):
        # This function retrieves the value for a given key from the cache 
        v = self.redis.get(k).decode('utf-8')
        return v