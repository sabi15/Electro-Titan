import discord
from database.db import get_pool
from utils.emojis import E_CORRECT, E_WRONG
from utils.helpers import normalize_tag
from cogs.acc.utils import maybe_send_invite


async def remove(interaction: discord.Interaction, tag: str):
   await interaction.response.defer()

   tag = normalize_tag(tag)
   pool = await get_pool()

   row = await pool.fetchrow(
       "SELECT discord_id, ign, th_level FROM acc_accounts WHERE tag = $1",
       tag
   )

   if not row:
       await interaction.followup.send(embed=discord.Embed(
           description=f"{E_WRONG} No account found for tag `{tag}`.",
           color=discord.Color.red()
       ))
       return

   if row["discord_id"] != interaction.user.id:
       await interaction.followup.send(embed=discord.Embed(
           description=f"{E_WRONG} You can only remove accounts that you have claimed.",
           color=discord.Color.red()
       ))
       return

   async with pool.acquire() as conn:
       async with conn.transaction():
           await conn.execute(
               "DELETE FROM acc_accounts WHERE tag = $1", tag
           )
           await conn.execute(
               """
               INSERT INTO acc_history (discord_id, tag, ign, th_level, action)
               VALUES ($1, $2, $3, $4, 'removed')
               """,
               interaction.user.id, tag, row["ign"], row["th_level"]
           )

   embed = discord.Embed(
       title="Account Unlinked",
       description=f"{E_CORRECT} **{row['ign']}** (`{tag}`) has been removed from your linked accounts.",
       color=discord.Color.orange()
   )
   embed.set_footer(text=f"Removed by {interaction.user.display_name}")
   await interaction.followup.send(embed=embed)

   invite = await maybe_send_invite(interaction.user.id, interaction.guild_id)
   if invite:
       await interaction.followup.send(invite)
