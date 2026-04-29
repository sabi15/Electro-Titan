import discord
from discord import app_commands
from discord.ext import commands
from database.db import get_pool
from config import BOT_DEV_ID


class DevMigrate(commands.Cog):
    @app_commands.command(name="dev-migrate", description="Drop and recreate all RIKA tables.")
    async def dev_migrate(self, interaction: discord.Interaction):
        if interaction.user.id != BOT_DEV_ID:
            await interaction.response.send_message("No permission.")
            return

        await interaction.response.send_message("Running migration...")

        pool = await get_pool()
        async with pool.acquire() as conn:

            # Drop in reverse dependency order
            await conn.execute("DROP TABLE IF EXISTS division_season_archive CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS division_participants CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS division_groups CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS division_schedules CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS division_settings CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS divisions CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS leagues CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS acc_usage CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS acc_history CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS acc_accounts CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS perm_assignments CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS disabled_cogs CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS whitelisted_servers CASCADE;")

            # whitelisted_servers
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS whitelisted_servers (
                    id         SERIAL PRIMARY KEY,
                    guild_id   TEXT NOT NULL UNIQUE,
                    added_at   TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # disabled_cogs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS disabled_cogs (
                    id       SERIAL PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    cog_name TEXT NOT NULL,
                    UNIQUE(guild_id, cog_name)
                );
            """)

            # perm_assignments
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS perm_assignments (
                    id         SERIAL PRIMARY KEY,
                    guild_id   TEXT NOT NULL,
                    role_id    TEXT NOT NULL,
                    permission TEXT NOT NULL,
                    UNIQUE(guild_id, role_id, permission)
                );
            """)

            # acc_accounts
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS acc_accounts (
                    id         SERIAL PRIMARY KEY,
                    guild_id   TEXT NOT NULL,
                    user_id    TEXT NOT NULL,
                    player_tag TEXT NOT NULL,
                    is_primary BOOLEAN DEFAULT FALSE,
                    claimed_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(guild_id, player_tag)
                );
            """)

            # acc_history
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS acc_history (
                    id         SERIAL PRIMARY KEY,
                    guild_id   TEXT NOT NULL,
                    user_id    TEXT NOT NULL,
                    player_tag TEXT NOT NULL,
                    action     TEXT NOT NULL,
                    acted_at   TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # acc_usage
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS acc_usage (
                    id         SERIAL PRIMARY KEY,
                    guild_id   TEXT NOT NULL,
                    user_id    TEXT NOT NULL,
                    command    TEXT NOT NULL,
                    used_at    TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # leagues
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS leagues (
                    id           SERIAL PRIMARY KEY,
                    guild_id     BIGINT NOT NULL,
                    name         TEXT NOT NULL,
                    code         TEXT NOT NULL,
                    description  TEXT,
                    logo_url     TEXT,
                    invite_link  TEXT,
                    ban_duration INTEGER,
                    created_at   TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(guild_id, code)
                );
            """)

            # divisions
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS divisions (
                    id                          SERIAL PRIMARY KEY,
                    guild_id                    TEXT NOT NULL,
                    league_code                 TEXT NOT NULL,
                    name                        TEXT NOT NULL,
                    code                        TEXT NOT NULL,
                    season                      TEXT NOT NULL DEFAULT '1',
                    logo_url                    TEXT,
                    transaction_log_channel_id  TEXT,
                    rep_role_id                 TEXT,
                    status                      TEXT NOT NULL DEFAULT 'active',
                    UNIQUE(guild_id, code)
                );
            """)

            # division_settings
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS division_settings (
                    id          SERIAL PRIMARY KEY,
                    division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                    key         TEXT NOT NULL,
                    value       TEXT,
                    UNIQUE(division_id, key)
                );
            """)

            # division_schedules
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS division_schedules (
                    id          SERIAL PRIMARY KEY,
                    division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                    name        TEXT NOT NULL,
                    start_date  DATE,
                    end_date    DATE,
                    UNIQUE(division_id, name)
                );
            """)

            # division_groups
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS division_groups (
                    id            SERIAL PRIMARY KEY,
                    division_id   INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                    schedule_name TEXT NOT NULL,
                    group_name    TEXT NOT NULL,
                    team_codes    TEXT[] NOT NULL DEFAULT '{}',
                    UNIQUE(division_id, schedule_name, group_name)
                );
            """)

            # division_participants
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS division_participants (
                    id          SERIAL PRIMARY KEY,
                    division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                    team_code   TEXT NOT NULL,
                    season      TEXT NOT NULL,
                    timezone    TEXT,
                    UNIQUE(division_id, team_code, season)
                );
            """)

            # division_season_archive
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS division_season_archive (
                    id               SERIAL PRIMARY KEY,
                    division_id      INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
                    season           TEXT NOT NULL,
                    archived_at      TIMESTAMPTZ DEFAULT NOW(),
                    settings_snapshot JSONB,
                    groups_snapshot  JSONB
                );
            """)

        await interaction.followup.send("✅ Migration complete. All tables dropped and recreated.")
