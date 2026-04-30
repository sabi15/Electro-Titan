import discord
from database.db import get_pool


async def division_list(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    rows = await pool.fetch(
        """
        SELECT name, code, league_code, season
        FROM divisions
        WHERE guild_id = $1 AND status = 'active'
        ORDER BY league_code, name
        """,
        guild_id
    )

    if not rows:
        await interaction.response.send_message("No active divisions found in this server.")
        return

    grouped = {}
    for row in rows:
        lc = row["league_code"]
        if lc not in grouped:
            grouped[lc] = []
        grouped[lc].append(row)

    embed = discord.Embed(
        title="Active Divisions",
        color=discord.Color.blurple()
    )

    for league_code, divisions in grouped.items():
        lines = []
        for d in divisions:
            lines.append(f"**{d['name']}** • `{d['code']}` • Season `{d['season']}`")
        embed.add_field(name=f"League: {league_code}", value="\n".join(lines), inline=False)

    await interaction.response.send_message(embed=embed)
