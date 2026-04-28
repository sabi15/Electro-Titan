import discord
from database.db import get_pool
from cogs.league.utils import get_league


async def league_info(interaction: discord.Interaction, code: str):
    code = code.upper()
    league = await get_league(interaction.guild_id, code)
    if not league:
        await interaction.response.send_message(f"No league found with code `{code}`.")
        return

    pool = await get_pool()
    division_count = await pool.fetchval(
        "SELECT COUNT(*) FROM divisions WHERE league_code = $1 AND guild_id = $2",
        code, str(interaction.guild_id)
    ) or 0

    embed = discord.Embed(
        title=league['name'],
        description=league['description'] or "No description set.",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Code", value=f"`{league['code']}`", inline=True)
    embed.add_field(name="Divisions", value=str(division_count), inline=True)

    if league['invite_link']:
        embed.add_field(name="Server Invite", value=league['invite_link'], inline=False)

    if league['logo_url']:
        embed.set_thumbnail(url=league['logo_url'])

    embed.set_footer(text="League created in this server")
    await interaction.response.send_message(embed=embed)
