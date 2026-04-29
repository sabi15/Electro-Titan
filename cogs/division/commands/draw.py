import discord
import random
from database.db import get_pool
from cogs.division.utils import check_division_admin, get_division_by_code


async def division_draw(
    interaction: discord.Interaction,
    division: str,
    schedule_name: str,
    groups: int,
    by_timezone: bool = False
):
    if not await check_division_admin(interaction):
        await interaction.response.send_message("You don't have permission to do this.")
        return

    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    div = await get_division_by_code(pool, guild_id, division)
    if not div:
        await interaction.response.send_message(f"No division found with code `{division.upper()}`.")
        return

    schedule = await pool.fetchrow(
        "SELECT 1 FROM division_schedules WHERE division_id = $1 AND name = $2",
        div["id"], schedule_name
    )
    if not schedule:
        await interaction.response.send_message(f"No schedule named `{schedule_name}` found.")
        return

    participants = await pool.fetch(
        "SELECT team_code, timezone FROM division_participants WHERE division_id = $1 AND season = $2",
        div["id"], div["season"]
    )

    if not participants:
        await interaction.response.send_message(f"No participants found for **{div['name']}**.")
        return

    if groups < 1 or groups > len(participants):
        await interaction.response.send_message(f"Invalid group count. Must be between 1 and {len(participants)}.")
        return

    if by_timezone:
        tz_buckets = {}
        for p in participants:
            tz = p["timezone"] or "Unknown"
            tz_buckets.setdefault(tz, []).append(p["team_code"])
        teams_ordered = []
        for bucket in tz_buckets.values():
            random.shuffle(bucket)
            teams_ordered.extend(bucket)
    else:
        teams_ordered = [p["team_code"] for p in participants]
        random.shuffle(teams_ordered)

    group_buckets = [[] for _ in range(groups)]
    for i, team in enumerate(teams_ordered):
        group_buckets[i % groups].append(team)

    embed = discord.Embed(
        title=f"Draw Results — {div['name']}",
        description=f"Schedule: `{schedule_name}` | Groups: {groups}{' | By Timezone' if by_timezone else ''}",
        color=discord.Color.gold()
    )

    group_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i, bucket in enumerate(group_buckets):
        label = f"Group {group_labels[i]}" if i < len(group_labels) else f"Group {i + 1}"
        existing = await pool.fetchrow(
            "SELECT 1 FROM division_groups WHERE division_id = $1 AND schedule_name = $2 AND group_name = $3",
            div["id"], schedule_name, label
        )
        if not existing:
            await pool.execute(
                "INSERT INTO division_groups (division_id, schedule_name, group_name, team_codes) VALUES ($1, $2, $3, $4)",
                div["id"], schedule_name, label, bucket
            )
        else:
            await pool.execute(
                "UPDATE division_groups SET team_codes = $1 WHERE division_id = $2 AND schedule_name = $3 AND group_name = $4",
                bucket, div["id"], schedule_name, label
            )
        embed.add_field(name=label, value="\n".join(f"• `{t}`" for t in bucket), inline=True)

    await interaction.response.send_message(embed=embed)
