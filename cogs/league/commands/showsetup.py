import discord
from cogs.league.utils import check_league_admin, get_league


async def league_showsetup(interaction: discord.Interaction, code: str):
    if not await check_league_admin(interaction):
        await interaction.response.send_message("You don't have permission to use this command.")
        return

    code = code.upper()
    league = await get_league(interaction.guild_id, code)
    if not league:
        await interaction.response.send_message(f"No league found with code `{code}`.")
        return

    embed = discord.Embed(
        title=f"Setup Values — {league['name']} ({code})",
        color=discord.Color.blurple()
    )
    embed.add_field(name="📝 Description", value=league['description'] or "*Not set*", inline=False)
    embed.add_field(name="🔗 Server Invite Link", value=league['invite_link'] or "*Not set*", inline=False)
    embed.add_field(name="🏷️ Code", value=f"`{league['code']}`", inline=False)
    embed.add_field(name="⏱️ Ban Duration", value=f"{league['ban_duration']} days" if league['ban_duration'] else "*Not set*", inline=False)

    await interaction.response.send_message(embed=embed)
