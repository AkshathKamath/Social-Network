import redis

redis_client = redis.from_url('redis://localhost:6379/0')

def get_redis():
    return redis_client