import discord
from discord import app_commands
from database.db import get_pool
from config import BOT_DEV_ID


async def dev_migrate(interaction: discord.Interaction):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("No permission.")
        return

    await interaction.response.send_message("⚠️ Running division DB migration...")

    pool = await get_pool()
    async with pool.acquire() as conn:

        # 🔥 Drop tables in correct dependency order
        await conn.execute("DROP TABLE IF EXISTS division_season_archive CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS division_participants CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS division_groups CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS division_schedules CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS division_settings CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS divisions CASCADE;")

        # ✅ Recreate tables
        await conn.execute("""
            CREATE TABLE divisions (
                id SERIAL PRIMARY KEY,
                guild_id TEXT NOT NULL,
                league_code TEXT NOT NULL,
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                season TEXT NOT NULL DEFAULT '1',
                logo_url TEXT,
                transaction_log_channel_id TEXT,
                rep_role_id TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                UNIQUE(guild_id, code)
            );
        """)

        await conn.execute("""
            CREATE TABLE division_settings (
                id SERIAL PRIMARY KEY,
                division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                key TEXT NOT NULL,
                value TEXT,
                UNIQUE(division_id, key)
            );
        """)

        await conn.execute("""
            CREATE TABLE division_schedules (
                id SERIAL PRIMARY KEY,
                division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                start_date DATE,
                end_date DATE,
                UNIQUE(division_id, name)
            );
        """)

        await conn.execute("""
            CREATE TABLE division_groups (
                id SERIAL PRIMARY KEY,
                division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                schedule_name TEXT NOT NULL,
                group_name TEXT NOT NULL,
                team_codes TEXT[] NOT NULL DEFAULT '{}',
                UNIQUE(division_id, schedule_name, group_name)
            );
        """)

        await conn.execute("""
            CREATE TABLE division_participants (
                id SERIAL PRIMARY KEY,
                division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                team_code TEXT NOT NULL,
                season TEXT NOT NULL,
                timezone TEXT,
                UNIQUE(division_id, team_code, season)
            );
        """)

        await conn.execute("""
            CREATE TABLE division_season_archive (
                id SERIAL PRIMARY KEY,
                division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                season TEXT NOT NULL,
                archived_at TIMESTAMPTZ DEFAULT NOW(),
                settings_snapshot JSONB,
                groups_snapshot JSONB
            );
        """)

    await interaction.followup.send("✅ Division migration complete. All tables recreated.")
