import discord
from database.db import get_pool
from config import BOT_DEV_ID


async def whitelist(interaction: discord.Interaction, server_id: str):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    pool = await get_pool()

    await pool.execute(
        """INSERT INTO whitelisted_servers (server_id, whitelisted)
           VALUES ($1, TRUE)
           ON CONFLICT (server_id) DO UPDATE SET whitelisted=TRUE""",
        server_id
    )

    embed = discord.Embed(
        title="✅ Server Whitelisted",
        color=0x2ecc71
    )
    embed.add_field(name="Server ID", value=f"`{server_id}`", inline=False)
    await interaction.response.send_message(embed=embed)
