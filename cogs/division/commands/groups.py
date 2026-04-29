import discord
from discord.ext import commands
from discord import app_commands
from database.db import get_pool
from cogs.division.utils import get_division_by_code

class DivisionGroups(commands.Cog):
    @app_commands.command(name="division-groups", description="View all groups in a division.")
    @app_commands.describe(division="Division code")
    async def division_groups(self, interaction: discord.Interaction, division: str):
        guild_id = str(interaction.guild_id)
        pool = await get_pool()

        div = await get_division_by_code(pool, guild_id, division)
        if not div:
            await interaction.response.send_message(f"No division found with code `{division.upper()}`.")
            return

        rows = await pool.fetch(
            """
            SELECT schedule_name, group_name, team_codes
            FROM division_groups
            WHERE division_id = $1
            ORDER BY schedule_name, group_name
            """,
            div["id"]
        )

        if not rows:
            await interaction.response.send_message(f"No groups found for **{div['name']}**.")
            return

        embed = discord.Embed(title=f"Groups — {div['name']}", color=discord.Color.blurple())

        schedules = {}
        for row in rows:
            sn = row["schedule_name"]
            if sn not in schedules:
                schedules[sn] = []
            schedules[sn].append(f"**{row['group_name']}**: {', '.join(row['team_codes'])}")

        for sched, lines in schedules.items():
            embed.add_field(name=f"📅 {sched}", value="\n".join(lines), inline=False)

        await interaction.response.send_message(embed=embed)
