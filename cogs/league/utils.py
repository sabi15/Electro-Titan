from database.db import get_pool


async def get_league(guild_id: int, code: str):
    pool = await get_pool()
    return await pool.fetchrow(
        "SELECT * FROM leagues WHERE guild_id = $1 AND code = $2",
        guild_id, code.upper()
    )


async def check_league_admin(interaction):
    from config import BOT_DEV_ID
    if interaction.user.id == BOT_DEV_ID:
        return True

    pool = await get_pool()
    role_ids = [str(role.id) for role in interaction.user.roles]
    if not role_ids:
        return False

    row = await pool.fetchrow(
        """
        SELECT 1 FROM perm_assignments
        WHERE guild_id = $1
        AND role_id = ANY($2::text[])
        AND permission = 'LEAGUE_ADMIN'
        """,
        str(interaction.guild_id), role_ids
    )
    return row is not None
