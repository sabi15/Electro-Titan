import discord
from database.db import get_pool
from cogs.division.utils import check_division_admin, get_division_by_code


async def division_delete(interaction: discord.Interaction, code: str):
    if not await check_division_admin(interaction):
        await interaction.response.send_message("You don't have permission to delete divisions.")
        return

    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    division = await get_division_by_code(pool, guild_id, code)
    if not division:
        await interaction.response.send_message(f"No division found with code `{code.upper()}`.")
        return

    await pool.execute(
        "DELETE FROM divisions WHERE guild_id = $1 AND code = $2",
        guild_id, code.upper()
    )

    await interaction.response.send_message(
        embed=discord.Embed(
            title="Division Deleted",
            description=f"**{division['name']}** (`{code.upper()}`) has been permanently deleted.",
            color=discord.Color.red()
        )
    )
