import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_authorized, is_manage_or_admin


async def team_addlogo(interaction: discord.Interaction, logo: discord.Attachment, team_code: str = None):
    if not await check_access(interaction, "team"):
        return
    await interaction.response.defer()
    pool = await get_pool()
    gid = str(interaction.guild_id)

    if not logo.content_type or not logo.content_type.startswith("image/"):
        await interaction.followup.send(embed=discord.Embed(
            description="❌ Please upload a valid image file.",
            color=0xe74c3c
        ))
        return

    app = await get_app_by_channel(str(interaction.channel_id), gid)

    if app:
        # Inside an application channel — use that team
        if not await is_authorized(interaction, app):
            await interaction.followup.send(embed=discord.Embed(
                description="❌ You are not authorized to use this command here.",
                color=0xe74c3c
            ))
            return
        division_code = app['division_code']
        t_code = app['team_code']
    else:
        # Outside app channel — team_code required, must be manage/admin
        if not team_code:
            await interaction.followup.send(embed=discord.Embed(
                description="❌ Provide a team code when using this command outside an application channel.",
                color=0xe74c3c
            ))
            return
        if not await is_manage_or_admin(interaction):
            await interaction.followup.send(embed=discord.Embed(
                description="❌ You need MANAGE_APPLICATIONS or DIVISION_ADMIN to use this outside an application channel.",
                color=0xe74c3c
            ))
            return
        t_code = team_code.strip().upper()
        team_row = await pool.fetchrow(
            "SELECT * FROM teams WHERE guild_id=$1 AND team_code=$2",
            gid, t_code
        )
        if not team_row:
            await interaction.followup.send(embed=discord.Embed(
                description=f"❌ Team **{t_code}** not found.",
                color=0xe74c3c
            ))
            return
        division_code = team_row['division_code']

    await pool.execute(
        "UPDATE teams SET logo_url=$1 WHERE guild_id=$2 AND division_code=$3 AND team_code=$4",
        logo.url, gid, division_code, t_code
    )

    embed = discord.Embed(
        description=f"✅ Logo updated for team **{t_code}**.",
        color=0x2ecc71
    )
    embed.set_thumbnail(url=logo.url)
    await interaction.followup.send(embed=embed)
