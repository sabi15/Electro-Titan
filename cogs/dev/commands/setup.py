import discord
from database.db import get_pool
from config import BOT_DEV_ID

TOGGLEABLE_COGS = [
    "division", "export", "feed", "fp",
    "league", "match", "banner",
    "schedule", "team", "transaction",
    "blist", "panel"
]


async def setup(interaction: discord.Interaction):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    pool = await get_pool()
    gid = str(interaction.guild_id)

    disabled = await pool.fetch(
        "SELECT cog_name FROM disabled_cogs WHERE server_id=$1",
        gid
    )
    disabled_names = [r["cog_name"] for r in disabled]
    enabled_names = [c for c in TOGGLEABLE_COGS if c not in disabled_names]

    whitelisted = await pool.fetchrow(
        "SELECT whitelisted FROM whitelisted_servers WHERE server_id=$1",
        gid
    )
    status = "✅ Whitelisted" if whitelisted and whitelisted["whitelisted"] else "🚫 Not Whitelisted"

    embed = discord.Embed(
        title="⚙️ Server Setup",
        color=0x2b2d31
    )
    embed.add_field(name="Server Name", value=interaction.guild.name, inline=False)
    embed.add_field(name="Server ID", value=f"`{gid}`", inline=False)
    embed.add_field(name="Whitelist Status", value=status, inline=False)
    embed.add_field(
        name="✅ Enabled Cogs",
        value=", ".join(f"`{c}`" for c in enabled_names) or "None",
        inline=False
    )
    embed.add_field(
        name="🔴 Disabled Cogs",
        value=", ".join(f"`{c}`" for c in disabled_names) or "None",
        inline=False
    )
    await interaction.response.send_message(embed=embed)
