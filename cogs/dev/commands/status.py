import discord
from database.db import get_pool
from config import BOT_DEV_ID


async def status(interaction: discord.Interaction):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    await interaction.response.defer()
    pool = await get_pool()

    total_claims = await pool.fetchval("SELECT COUNT(*) FROM claims")
    total_guilds = len(interaction.client.guilds)
    latency = round(interaction.client.latency * 1000)

    embed = discord.Embed(
        title="📊 RIKA Status",
        color=0x2b2d31
    )
    embed.add_field(name="🏓 Latency", value=f"`{latency}ms`", inline=True)
    embed.add_field(name="🌐 Servers", value=f"`{total_guilds}`", inline=True)
    embed.add_field(name="🎮 Accounts Claimed", value=f"`{total_claims}`", inline=True)
    embed.set_footer(text="RIKA Bot")
    await interaction.followup.send(embed=embed)
