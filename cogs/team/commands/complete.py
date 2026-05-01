import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_authorized, get_division_setting, get_division_by_code


async def team_complete(interaction: discord.Interaction):
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

    if app['status'] == 'completed':
        await interaction.followup.send(embed=discord.Embed(
            description="❌ This application is already marked as complete.",
            color=0xe74c3c
        ))
        return

    team = await pool.fetchrow(
        "SELECT * FROM teams WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
        gid, app['division_code'], app['team_code']
    )
    roster_count = await pool.fetchval(
        "SELECT COUNT(*) FROM rosters WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
        gid, app['division_code'], app['team_code']
    )

    div = await get_division_by_code(gid, app['division_code'])
    min_roster = await get_division_setting(div['id'], 'min_roster')
    require_secondary = await get_division_setting(div['id'], 'allow_secondary_clan')

    issues = []
    if min_roster and roster_count < int(min_roster):
        issues.append(f"Roster too small: **{roster_count}**/{min_roster}")
    if not team or not team['main_clan']:
        issues.append("Main clan is not set")
    if require_secondary == 'true' and (not team or not team['secondary_clan']):
        issues.append("Secondary clan is not set")
    if not team or not team['timezone']:
        issues.append("Timezone is not set")
    if not team or not team['language']:
        issues.append("Language is not set")
    if not team or not team['logo_url']:
        issues.append("Logo is not set")

    if issues:
        desc = "❌ Your application is missing the following:\n\n" + "\n".join(f"⚠️ {i}" for i in issues)
        await interaction.followup.send(embed=discord.Embed(
            description=desc,
            color=0xe74c3c
        ))
        return

    await pool.execute(
        "UPDATE applications SET status='completed' WHERE id=$1",
        app['id']
    )

    try:
        new_name = f"🏳️-{app['team_name'].lower().replace(' ', '-')}"
        await interaction.channel.edit(name=new_name)
    except Exception:
        pass

    await interaction.followup.send(embed=discord.Embed(
        description=f"✅ **{app['team_name']}** application marked as complete and ready for review.",
        color=0x2ecc71
    ))
