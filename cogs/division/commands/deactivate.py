import discord
from database.db import get_pool
from cogs.division.utils import check_division_admin, get_division_by_code


async def division_deactivate(interaction: discord.Interaction, code: str):
    if not await check_division_admin(interaction):
        await interaction.response.send_message("You don't have permission to do this.")
        return

    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    division = await get_division_by_code(pool, guild_id, code)
    if not division:
        await interaction.response.send_message(f"No division found with code `{code.upper()}`.")
        return

    new_status = "inactive" if division["status"] == "active" else "active"
    await pool.execute(
        "UPDATE divisions SET status = $1 WHERE guild_id = $2 AND code = $3",
        new_status, guild_id, code.upper()
    )

    color = discord.Color.green() if new_status == "active" else discord.Color.red()
    await interaction.response.send_message(
        embed=discord.Embed(
            title="Division Status Updated",
            description=f"**{division['name']}** is now **{new_status}**.",
            color=color
        )
    )
