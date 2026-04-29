import discord
from discord.ext import commands
from discord import app_commands
from database.db import get_pool
from cogs.division.utils import check_division_admin, get_division_by_code

class DivisionAddGroup(commands.Cog):
    @app_commands.command(name="division-addgroup", description="Add a group to a schedule in a division.")
    @app_commands.describe(
        division="Division code",
        schedule_name="Name of the schedule/stage",
        group_name="Name of the group (e.g. Group A)",
        team_codes="Comma-separated team codes (e.g. TSM,GBS1,NRG)"
    )
    async def division_addgroup(
        self,
        interaction: discord.Interaction,
        division: str,
        schedule_name: str,
        group_name: str,
        team_codes: str
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
            await interaction.response.send_message(f"No schedule named `{schedule_name}` found. Create the schedule first.")
            return

        codes = [c.strip().upper() for c in team_codes.split(",") if c.strip()]
        if not codes:
            await interaction.response.send_message("Provide at least one valid team code.")
            return

        existing = await pool.fetchrow(
            "SELECT 1 FROM division_groups WHERE division_id = $1 AND schedule_name = $2 AND group_name = $3",
            div["id"], schedule_name, group_name
        )
        if existing:
            await interaction.response.send_message(f"Group `{group_name}` already exists in schedule `{schedule_name}`.")
            return

        await pool.execute(
            """
            INSERT INTO division_groups (division_id, schedule_name, group_name, team_codes)
            VALUES ($1, $2, $3, $4)
            """,
            div["id"], schedule_name, group_name, codes
        )

        embed = discord.Embed(
            title="Group Added",
            color=discord.Color.green()
        )
        embed.add_field(name="Division", value=div["name"], inline=True)
        embed.add_field(name="Schedule", value=schedule_name, inline=True)
        embed.add_field(name="Group", value=group_name, inline=True)
        embed.add_field(name="Teams", value=", ".join(codes), inline=False)
        await interaction.response.send_message(embed=embed)
