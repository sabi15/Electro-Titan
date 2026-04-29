import discord
from database.db import get_pool
from cogs.division.utils import check_division_admin, get_division_by_code


async def division_setlogo(interaction: discord.Interaction, division: str, logo: str):
    if not await check_division_admin(interaction):
        await interaction.response.send_message("You don't have permission to do this.")
        return

    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    div = await get_division_by_code(pool, guild_id, division)
    if not div:
        await interaction.response.send_message(f"No division found with code `{division.upper()}`.")
        return

    await pool.execute(
        "UPDATE divisions SET logo_url = $1 WHERE guild_id = $2 AND code = $3",
        logo, guild_id, division.upper()
    )

    embed = discord.Embed(
        title="Logo Updated",
        description=f"Logo for **{div['name']}** has been updated.",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=logo)
    await interaction.response.send_message(embed=embed)
