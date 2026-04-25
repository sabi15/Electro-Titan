import discord
from database.db import get_pool
from config import BOT_DEV_ID


async def clearallperms(interaction: discord.Interaction):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    pool = await get_pool()
    gid = str(interaction.guild_id)

    await pool.execute(
        "DELETE FROM perm_assignments WHERE guild_id=$1",
        gid
    )

    embed = discord.Embed(
        title="✅ All Permissions Cleared",
        description=f"All perm assignments for **{interaction.guild.name}** have been removed.",
        color=0xe74c3c
    )
    await interaction.response.send_message(embed=embed)
