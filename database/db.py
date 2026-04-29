import asyncpg
import os
from config import DATABASE_URL

_pool = None

async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL)
    await create_tables()

async def create_tables():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema = f.read()
    async with _pool.acquire() as conn:
        await conn.execute(schema)



async def get_pool():
    return _pool
