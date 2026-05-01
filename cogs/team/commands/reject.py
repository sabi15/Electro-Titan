import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_manage_or_admin


async def team_reject(interaction: discord.Interaction, reason: str):
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

    if not await is_manage_or_admin(interaction):
        await interaction.followup.send(embed=discord.Embed(
            description="❌ Requires MANAGE_APPLICATIONS or DIVISION_ADMIN.",
            color=0xe74c3c
        ))
        return

    if app['status'] in ('rejected', 'accepted', 'withdrawn'):
        await interaction.followup.send(embed=discord.Embed(
            description=f"❌ This application is already **{app['status']}**.",
            color=0xe74c3c
        ))
        return

    await pool.execute("UPDATE applications SET status='rejected' WHERE id=$1", app['id'])

    try:
        new_name = f"❌-{app['team_name'].lower().replace(' ', '-')}"
        await interaction.channel.edit(name=new_name)
    except Exception:
        pass

    await interaction.channel.send(f"<@{app['rep_id']}>")

    await interaction.channel.send(embed=discord.Embed(
        title="❌ Application Rejected",
        description=f"**{app['team_name']}**'s application has been rejected.\n\n**Reason:** {reason}",
        color=0xe74c3c
    ))

    await interaction.followup.send(embed=discord.Embed(
        description=f"✅ **{app['team_name']}** has been rejected.",
        color=0x2ecc71
    ))
