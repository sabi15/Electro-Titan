import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_authorized


async def team_setrep(interaction: discord.Interaction, user: discord.Member, slot: str):
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

   col = "rep_id" if slot == "1" else "rep2_id"
   await pool.execute(
       f"UPDATE teams SET {col}=$1 WHERE guild_id=$2 AND division_code=$3 AND team_code=$4",
       str(user.id), gid, app['division_code'], app['team_code']
   )

   if slot == "1":
       await pool.execute(
           "UPDATE applications SET rep_id=$1 WHERE id=$2",
           str(user.id), app['id']
       )
       try:
           old_rep = interaction.guild.get_member(int(app['rep_id']))
           if old_rep and old_rep.id != user.id:
               await interaction.channel.set_permissions(old_rep, overwrite=None)
           await interaction.channel.set_permissions(
               user, view_channel=True, send_messages=True, read_message_history=True
           )
       except Exception:
           pass

   slot_label = "Representative 1" if slot == "1" else "Representative 2"
   await interaction.followup.send(embed=discord.Embed(
       description=f"✅ **{slot_label}** set to {user.mention}.",
       color=0x2ecc71
   ))
