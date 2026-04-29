import asyncio
import asyncpg
from config import DATABASE_URL

async def reset():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        DROP TABLE IF EXISTS acc_accounts CASCADE;
        DROP TABLE IF EXISTS acc_history CASCADE;
        DROP TABLE IF EXISTS acc_usage CASCADE;
    """)
    await conn.close()
    print("✅ Done! Restart your bot now.")

asyncio.run(reset())
