import discord
from discord import app_commands
from database.db import get_pool
from config import BOT_DEV_ID


async def dev_migrate(interaction: discord.Interaction):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("No permission.")
        return

    await interaction.response.send_message("Running migration...")

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS leagues;")
        await conn.execute("""
            CREATE TABLE leagues (
                id           SERIAL PRIMARY KEY,
                guild_id     BIGINT NOT NULL,
                name         TEXT NOT NULL,
                code         TEXT NOT NULL,
                description  TEXT,
                logo_url     TEXT,
                invite_link  TEXT,
                ban_duration INTEGER,
                created_at   TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (guild_id, code)
            );
        """)

    await interaction.followup.send("✅ Migration complete. `leagues` table recreated.")
