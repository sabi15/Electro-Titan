import discord
from database.db import get_pool
from cogs.division.utils import get_division_by_code


async def division_participants(interaction: discord.Interaction, division: str):
    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    div = await get_division_by_code(pool, guild_id, division)
    if not div:
        await interaction.response.send_message(f"No division found with code `{division.upper()}`.")
        return

    rows = await pool.fetch(
        """
        SELECT team_code, timezone FROM division_participants
        WHERE division_id = $1 AND season = $2
        ORDER BY team_code
        """,
        div["id"], div["season"]
    )

    if not rows:
        await interaction.response.send_message(f"No participants found for **{div['name']}** season `{div['season']}`.")
        return

    lines = []
    for row in rows:
        tz = f" ({row['timezone']})" if row["timezone"] else ""
        lines.append(f"• `{row['team_code']}`{tz}")

    embed = discord.Embed(
        title=f"Participants — {div['name']} (Season {div['season']})",
        description="\n".join(lines),
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed)
