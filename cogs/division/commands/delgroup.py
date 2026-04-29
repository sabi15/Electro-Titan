import discord
from database.db import get_pool
from cogs.division.utils import check_division_admin, get_division_by_code


async def division_delgroup(
    interaction: discord.Interaction,
    division: str,
    schedule_name: str,
    group_name: str
):
    if not await check_division_admin(interaction):
        await interaction.response.send_message("You don't have permission to do this.")
        return

    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    div = await get_division_by_code(pool, guild_id, division)
    if not div:
        await interaction.response.send_message(f"No division found with code `{division.upper()}`.")
        return

    group = await pool.fetchrow(
        "SELECT 1 FROM division_groups WHERE division_id = $1 AND schedule_name = $2 AND group_name = $3",
        div["id"], schedule_name, group_name
    )
    if not group:
        await interaction.response.send_message(f"No group `{group_name}` found in schedule `{schedule_name}`.")
        return

    await pool.execute(
        "DELETE FROM division_groups WHERE division_id = $1 AND schedule_name = $2 AND group_name = $3",
        div["id"], schedule_name, group_name
    )

    await interaction.response.send_message(
        embed=discord.Embed(
            title="Group Deleted",
            description=f"Group **{group_name}** removed from schedule `{schedule_name}` in **{div['name']}**.",
            color=discord.Color.red()
        )
    )
