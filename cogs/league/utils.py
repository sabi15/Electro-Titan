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
    row = await pool.fetchrow(
        """
        SELECT 1 FROM perm_assignments
        WHERE guild_id = $1 AND discord_id = $2 AND permission = 'LEAGUE_ADMIN'
        """,
        interaction.guild_id, interaction.user.id
    )
    return row is not None
