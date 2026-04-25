import discord
from database.db import get_pool
from config import BOT_DEV_ID


async def permlist(interaction: discord.Interaction):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    pool = await get_pool()
    gid = str(interaction.guild_id)

    rows = await pool.fetch(
        "SELECT role_id, permission FROM perm_assignments WHERE guild_id=$1 ORDER BY permission",
        gid
    )

    if not rows:
        await interaction.response.send_message(
            "❌ No permissions assigned in this server.",
        )
        return

    grouped = {}
    for row in rows:
        perm = row["permission"]
        role_id = row["role_id"]
        grouped.setdefault(perm, []).append(f"<@&{role_id}>")

    embed = discord.Embed(
        title=f"🔐 Permission List — {interaction.guild.name}",
        color=0x2b2d31
    )
    for perm, roles in grouped.items():
        embed.add_field(
            name=f"`{perm}`",
            value=" ".join(roles),
            inline=False
        )

    await interaction.response.send_message(embed=embed)
