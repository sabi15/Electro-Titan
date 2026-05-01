from config import BOT_DEV_ID
from database.db import get_pool


async def get_app_by_channel(channel_id: str, guild_id: str):
    pool = await get_pool()
    return await pool.fetchrow(
        "SELECT * FROM applications WHERE guild_id=$1 AND channel_id=$2 AND status NOT IN ('rejected','withdrawn')",
        guild_id, channel_id
    )


async def is_authorized(interaction, app) -> bool:
    """Returns True if user is BOT_DEV, rep1, rep2, MANAGE_APPLICATIONS, or DIVISION_ADMIN."""
    if interaction.user.id == BOT_DEV_ID:
        return True
    if str(interaction.user.id) == app['rep_id']:
        return True
    if app['rep2_id'] and str(interaction.user.id) == app['rep2_id']:
        return True
    pool = await get_pool()
    role_ids = [str(r.id) for r in interaction.user.roles]
    if not role_ids:
        return False
    row = await pool.fetchrow(
        """
        SELECT 1 FROM perm_assignments
        WHERE guild_id=$1
        AND role_id = ANY($2::text[])
        AND permission IN ('MANAGE_APPLICATIONS', 'DIVISION_ADMIN')
        """,
        str(interaction.guild_id), role_ids
    )
    return row is not None


async def is_manage_or_admin(interaction) -> bool:
    """Returns True if user is BOT_DEV, MANAGE_APPLICATIONS, or DIVISION_ADMIN."""
    if interaction.user.id == BOT_DEV_ID:
        return True
    pool = await get_pool()
    role_ids = [str(r.id) for r in interaction.user.roles]
    if not role_ids:
        return False
    row = await pool.fetchrow(
        """
        SELECT 1 FROM perm_assignments
        WHERE guild_id=$1
        AND role_id = ANY($2::text[])
        AND permission IN ('MANAGE_APPLICATIONS', 'DIVISION_ADMIN')
        """,
        str(interaction.guild_id), role_ids
    )
    return row is not None


async def is_division_admin(interaction) -> bool:
    """Returns True if user is BOT_DEV or DIVISION_ADMIN."""
    if interaction.user.id == BOT_DEV_ID:
        return True
    pool = await get_pool()
    role_ids = [str(r.id) for r in interaction.user.roles]
    if not role_ids:
        return False
    row = await pool.fetchrow(
        """
        SELECT 1 FROM perm_assignments
        WHERE guild_id=$1
        AND role_id = ANY($2::text[])
        AND permission = 'DIVISION_ADMIN'
        """,
        str(interaction.guild_id), role_ids
    )
    return row is not None


async def get_division_setting(division_id: int, key: str) -> str | None:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT value FROM division_settings WHERE division_id=$1 AND key=$2",
        division_id, key
    )
    return row['value'] if row else None


async def get_division_by_code(guild_id: str, code: str):
    pool = await get_pool()
    return await pool.fetchrow(
        "SELECT * FROM divisions WHERE guild_id=$1 AND code=$2",
        guild_id, code
    )
