import aioredis


async def get_redis_pool() -> aioredis.Redis:
    redis = await aioredis.create_redis_pool("redis://redis:6379/0?encoding=utf-8")

    return redis
