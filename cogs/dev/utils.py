import discord
from database.db import get_pool
from config import BOT_DEV_ID, WHITELIST_MESSAGE, VALID_PERMS


async def is_dev(interaction: discord.Interaction) -> bool:
    return interaction.user.id == BOT_DEV_ID


async def is_whitelisted(guild_id: str) -> bool:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT whitelisted FROM whitelisted_servers WHERE server_id=$1",
        guild_id
    )
    if not row:
        return False
    return row["whitelisted"]


async def check_access(interaction: discord.Interaction, perm: str) -> bool:
    pool = await get_pool()
    gid = str(interaction.guild_id)

    if interaction.user.id == BOT_DEV_ID:
        return True

    if not await is_whitelisted(gid):
        await interaction.response.send_message(
            WHITELIST_MESSAGE,
        )
        return False

    user_role_ids = [str(r.id) for r in interaction.user.roles]
    rows = await pool.fetch(
        """SELECT 1 FROM perm_assignments
           WHERE guild_id=$1 AND permission=$2
           AND role_id = ANY($3::text[])""",
        gid, perm, user_role_ids
    )
    if not rows:
        await interaction.response.send_message(
            f"❌ You don't have the `{perm}` permission.",
        )
        return False

    return True
