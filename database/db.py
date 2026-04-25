import asyncpg
from config import DATABASE_URL

_pool = None

async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL)

async def get_pool():
    return _pool
