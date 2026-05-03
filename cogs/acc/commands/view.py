import discord
from database.db import get_pool
from utils.emojis import get_th_emoji, E_WRONG
from utils.helpers import normalize_tag
from cogs.acc.utils import maybe_send_invite
from datetime import timezone


async def view(interaction: discord.Interaction, tag: str = None, user: discord.Member = None):
   await interaction.response.defer()

   if tag is None and user is None:
       user = interaction.user

   pool = await get_pool()

   if tag:
       tag = normalize_tag(tag)

       row = await pool.fetchrow(
           """
           SELECT discord_id, ign, th_level, claimed_at
           FROM acc_accounts
           WHERE tag = $1
           """,
           tag
       )

       if not row:
           await interaction.followup.send(embed=discord.Embed(
               description=f"{E_WRONG} No account found for tag `{tag}`.",
               color=discord.Color.red()
           ))
           return

       th_emoji = get_th_emoji(row["th_level"])
       claimed_ts = int(row["claimed_at"].replace(tzinfo=timezone.utc).timestamp())
       try:
           member = interaction.guild.get_member(row["discord_id"]) or await interaction.guild.fetch_member(row["discord_id"])
           owner_display = member.mention
       except Exception:
           member = None
           owner_display = f"<@{row['discord_id']}>"

       embed = discord.Embed(title="Account Lookup", color=discord.Color.blurple())
       if member:
           embed.set_thumbnail(url=member.display_avatar.url)
       embed.add_field(
           name="Account",
           value=f"{th_emoji} **{row['ign']}** (`{tag}`)",
           inline=False
       )
       embed.add_field(name="Claimed By", value=owner_display, inline=True)
       embed.add_field(name="Claimed Since", value=f"<t:{claimed_ts}:D>", inline=True)
       await interaction.followup.send(embed=embed)

   else:
       rows = await pool.fetch(
           """
           SELECT tag, ign, th_level, claimed_at
           FROM acc_accounts
           WHERE discord_id = $1
           ORDER BY claimed_at ASC
           """,
           user.id
       )

       if not rows:
           await interaction.followup.send(embed=discord.Embed(
               description=f"{E_WRONG} {user.mention} has no linked accounts.",
               color=discord.Color.red()
           ))
           return

       embed = discord.Embed(
           title=f"Linked Accounts — {user.display_name}",
           color=discord.Color.blurple()
       )
       embed.set_thumbnail(url=user.display_avatar.url)
       lines = []
       for row in rows:
           th_emoji = get_th_emoji(row["th_level"])
           claimed_ts = int(row["claimed_at"].replace(tzinfo=timezone.utc).timestamp())
           lines.append(f"{th_emoji} **{row['ign']}** (`{row['tag']}`) — since <t:{claimed_ts}:D>")

       embed.description = "\n".join(lines)
       embed.set_footer(text=f"{len(rows)} account(s) linked")
       await interaction.followup.send(embed=embed)

   invite = await maybe_send_invite(interaction.user.id, interaction.guild_id)
   if invite:
       await interaction.followup.send(invite)
