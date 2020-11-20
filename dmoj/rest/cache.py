from typing import Union
import json

from dmoj.rest.app import app

KEY_PREFIX = 'submission:'


async def set(key: str, value: Union[str, dict], timeout: int):
    key = KEY_PREFIX + key
    if isinstance(value, dict):
        value = json.dumps(value)
    return await app.state.redis.set(key, value, timeout)


async def get(key: str):
    key = KEY_PREFIX + key
    return await app.state.redis.get(key, encoding='utf-8')
