import discord
from database.db import get_pool


async def league_list(interaction: discord.Interaction):
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT name, code, description FROM leagues WHERE guild_id = $1 ORDER BY created_at ASC",
        interaction.guild_id
    )

    if not rows:
        await interaction.response.send_message("No leagues have been created in this server yet.")
        return

    embed = discord.Embed(
        title="Leagues",
        color=discord.Color.blurple()
    )
    for row in rows:
        desc = row['description'] or "No description set."
        embed.add_field(
            name=f"{row['name']} ({row['code']})",
            value=desc,
            inline=False
        )

    await interaction.response.send_message(embed=embed)
