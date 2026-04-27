import discord
from cogs.league.utils import check_league_admin, get_league
from db import get_pool


async def league_addlogo(interaction: discord.Interaction, code: str, attachment: discord.Attachment):
    if not await check_league_admin(interaction):
        await interaction.response.send_message("You don't have permission to use this command.")
        return

    code = code.upper()
    league = await get_league(interaction.guild_id, code)
    if not league:
        await interaction.response.send_message(f"No league found with code `{code}`.")
        return

    if not attachment.content_type or not attachment.content_type.startswith("image/"):
        await interaction.response.send_message("Please upload a valid image file.")
        return

    pool = await get_pool()
    await pool.execute(
        "UPDATE leagues SET logo_url = $1 WHERE guild_id = $2 AND code = $3",
        attachment.url, interaction.guild_id, code
    )

    embed = discord.Embed(
        title="Logo Updated",
        description=f"Logo for **{league['name']}** (`{code}`) has been updated.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=attachment.url)
    await interaction.response.send_message(embed=embed)
