import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_authorized


async def team_setlanguage(interaction: discord.Interaction, language: str):
    if not await check_access(interaction, "team"):
        return
    await interaction.response.defer()
    pool = await get_pool()
    gid = str(interaction.guild_id)

    app = await get_app_by_channel(str(interaction.channel_id), gid)
    if not app:
        await interaction.followup.send(embed=discord.Embed(
            description="❌ Use this command inside an application channel.",
            color=0xe74c3c
        ))
        return

    if not await is_authorized(interaction, app):
        await interaction.followup.send(embed=discord.Embed(
            description="❌ You are not authorized to use this command here.",
            color=0xe74c3c
        ))
        return

    await pool.execute(
        "UPDATE teams SET language=$1 WHERE guild_id=$2 AND division_code=$3 AND team_code=$4",
        language.strip(), gid, app['division_code'], app['team_code']
    )
    await interaction.followup.send(embed=discord.Embed(
        description=f"✅ Team language set to **{language.strip()}**.",
        color=0x2ecc71
    ))
