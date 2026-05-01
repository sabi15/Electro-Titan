import discord
import coc
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_authorized
from utils.helpers import normalize_tag


async def team_delplayer(interaction: discord.Interaction, tag: str):
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

    tag = normalize_tag(tag)

    existing = await pool.fetchrow(
        "SELECT * FROM rosters WHERE guild_id=$1 AND division_code=$2 AND team_code=$3 AND player_tag=$4",
        gid, app['division_code'], app['team_code'], tag
    )
    if not existing:
        await interaction.followup.send(embed=discord.Embed(
            description=f"❌ `{tag}` is not on **{app['team_name']}**'s roster.",
            color=0xe74c3c
        ))
        return

    try:
        player = await interaction.client.coc_client.get_player(tag)
        player_name = player.name
        th = player.town_hall
    except Exception:
        player_name = tag
        th = 0

    await pool.execute(
        "DELETE FROM rosters WHERE guild_id=$1 AND division_code=$2 AND team_code=$3 AND player_tag=$4",
        gid, app['division_code'], app['team_code'], tag
    )

    from utils.emojis import get_th_emoji
    th_emoji = get_th_emoji(th)
    await interaction.followup.send(embed=discord.Embed(
        description=f"✅ {th_emoji} **{player_name}** (`{tag}`) removed from **{app['team_name']}**.",
        color=0x2ecc71
    ))
