import discord
import coc
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_authorized, get_division_setting, get_division_by_code
from utils.helpers import normalize_tag
from utils.emojis import E_CORRECT, E_WRONG


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

   await pool.execute(
       f"UPDATE teams SET {col}=$1 WHERE guild_id=$2 AND division_code=$3 AND team_code=$4",
       tag, gid, app['division_code'], app['team_code']
   )

   clan_link = f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={tag.replace('#', '')}"
   await interaction.followup.send(embed=discord.Embed(
       description=f"{E_CORRECT} **{clan_type.capitalize()} Clan** of **{app['team_name']}** is set to Lv.**{clan.level}** **{clan.name}**[link]({clan_link})**.",
       color=0x6BBF73
   ))
