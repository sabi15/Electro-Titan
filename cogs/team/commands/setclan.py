import discord
import coc
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_authorized, get_division_setting, get_division_by_code
from utils.helpers import normalize_tag
from utils.emojis import E_CORRECT, E_WRONG, E_INFO


async def team_setclan(interaction: discord.Interaction, clan_tag: str, clan_type: str):
    if not await check_access(interaction, "team"):
        return
    await interaction.response.defer()
    pool = await get_pool()
    gid = str(interaction.guild_id)

    app = await get_app_by_channel(str(interaction.channel_id), gid)
    if not app:
        await interaction.followup.send(embed=discord.Embed(
            description=f"{E_WRONG} Use this command inside an application channel.",
            color=0xe74c3c
        ))
        return

    if not await is_authorized(interaction, app):
        await interaction.followup.send(embed=discord.Embed(
            description=f"{E_WRONG} You are not authorized to use this command here.",
            color=0xe74c3c
        ))
        return

    tag = normalize_tag(clan_tag)

    if clan_type == "secondary":
        div = await get_division_by_code(gid, app['division_code'])
        allowed = await get_division_setting(div['id'], 'allow_secondary_clan')
        if not allowed or allowed.lower() != 'true':
            await interaction.followup.send(embed=discord.Embed(
                description=f"{E_WRONG} Secondary clans are not allowed in this division.",
                color=0xe74c3c
            ))
            return

    try:
        clan = await interaction.client.coc_client.get_clan(tag)
    except coc.NotFound:
        await interaction.followup.send(embed=discord.Embed(
            description=f"{E_WRONG} Clan not found. Check the tag and try again.",
            color=0xe74c3c
        ))
        return
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(
            description=f"{E_WRONG} CoC API error: {e}",
            color=0xe74c3c
        ))
        return

    col = "main_clan" if clan_type == "main" else "secondary_clan"
    other_col = "secondary_clan" if clan_type == "main" else "main_clan"
    other_type = "Secondary" if clan_type == "main" else "Main"

    team_row = await pool.fetchrow(
        "SELECT main_clan, secondary_clan FROM teams WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
        gid, app['division_code'], app['team_code']
    )

    current_same = team_row[col] if team_row else None
    current_other = team_row[other_col] if team_row else None

    # Case 1: Same tag already set on same type — remove it (only if not the only clan)
    if current_same == tag:
        if clan_type == "main" and not current_other:
            await interaction.followup.send(embed=discord.Embed(
                description=f"{E_WRONG} Can't remove your only Main Clan. Set a Secondary Clan first or replace it with a different tag.",
                color=0xe74c3c
            ))
            return
        await pool.execute(
            f"UPDATE teams SET {col}=NULL WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
            gid, app['division_code'], app['team_code']
        )
        await interaction.followup.send(embed=discord.Embed(
            description=f"{E_INFO} **{clan.name}** was already set as your **{clan_type.capitalize()} Clan** — it has been removed.",
            color=0x3498db
        ))
        return

    # Case 2: Same tag already set on other type — swap them (only if not demoting the only main)
    if current_other == tag:
        if clan_type == "secondary" and not current_same:
            await interaction.followup.send(embed=discord.Embed(
                description=f"{E_WRONG} Can't move your only Main Clan to Secondary. Set a new Main Clan first.",
                color=0xe74c3c
            ))
            return
        await pool.execute(
            f"UPDATE teams SET {col}=$1, {other_col}=NULL WHERE guild_id=$2 AND division_code=$3 AND team_code=$4",
            tag, gid, app['division_code'], app['team_code']
        )
        await interaction.followup.send(embed=discord.Embed(
            description=f"{E_INFO} **{clan.name}** was your **{other_type} Clan** — swapped to **{clan_type.capitalize()} Clan**.",
            color=0x3498db
        ))
        return

    # Case 3: Tag used by another team in this division
    other = await pool.fetchrow(
        f"SELECT team_code FROM teams WHERE guild_id=$1 AND division_code=$2 AND {col}=$3 AND team_code!=$4",
        gid, app['division_code'], tag, app['team_code']
    )
    if other:
        await interaction.followup.send(embed=discord.Embed(
            description=f"{E_WRONG} Clan `{tag}` is already registered by team **{other['team_code']}**.",
            color=0xe74c3c
        ))
        return

    # Default: set the clan
    await pool.execute(
        f"UPDATE teams SET {col}=$1 WHERE guild_id=$2 AND division_code=$3 AND team_code=$4",
        tag, gid, app['division_code'], app['team_code']
    )

    clan_link = f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={tag.replace('#', '')}"
    await interaction.followup.send(embed=discord.Embed(
        description=f"{E_CORRECT} {clan_type.capitalize()} Clan is set to Lv.{clan.level} {clan.name} ([link]({clan_link})).",
        color=0x6BBF73
    ))
