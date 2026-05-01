import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_authorized


async def team_withdraw(interaction: discord.Interaction):
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

    if app['status'] == 'accepted':
        await interaction.followup.send(embed=discord.Embed(
            description="❌ This application has already been accepted and cannot be withdrawn.",
            color=0xe74c3c
        ))
        return

    await pool.execute("UPDATE applications SET status='withdrawn' WHERE id=$1", app['id'])
    await pool.execute(
        "DELETE FROM rosters WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
        gid, app['division_code'], app['team_code']
    )
    await pool.execute(
        "DELETE FROM teams WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
        gid, app['division_code'], app['team_code']
    )

    await interaction.followup.send(embed=discord.Embed(
        description=f"✅ Application for **{app['team_name']}** has been withdrawn.",
        color=0x2ecc71
    ))

    try:
        await interaction.channel.delete()
    except Exception:
        pass
