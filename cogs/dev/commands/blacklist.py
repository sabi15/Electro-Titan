import discord
from database.db import get_pool
from config import BOT_DEV_ID


async def blacklist(interaction: discord.Interaction, server_id: str):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    pool = await get_pool()

    await pool.execute(
        """INSERT INTO whitelisted_servers (server_id, whitelisted)
           VALUES ($1, FALSE)
           ON CONFLICT (server_id) DO UPDATE SET whitelisted=FALSE""",
        server_id
    )

    guild = interaction.client.get_guild(int(server_id))
    if guild:
        try:
            await guild.leave()
        except Exception:
            pass

    embed = discord.Embed(
        title="🚫 Server Blacklisted",
        color=0xe74c3c
    )
    embed.add_field(name="Server ID", value=f"`{server_id}`", inline=False)
    embed.set_footer(text="Bot has left the server if it was present.")
    await interaction.response.send_message(embed=embed)
