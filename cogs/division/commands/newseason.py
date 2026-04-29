import discord
from discord.ext import commands
from discord import app_commands
import json
from database.db import get_pool
from cogs.division.utils import check_division_admin, get_division_by_code, get_division_settings

class DivisionNewSeason(commands.Cog):
    @app_commands.command(name="division-newseason", description="Archive current season and start fresh.")
    @app_commands.describe(code="The division code")
    async def division_newseason(self, interaction: discord.Interaction, code: str):
        if not await check_division_admin(interaction):
            await interaction.response.send_message("You don't have permission to do this.")
            return

        guild_id = str(interaction.guild_id)
        pool = await get_pool()

        division = await get_division_by_code(pool, guild_id, code)
        if not division:
            await interaction.response.send_message(f"No division found with code `{code.upper()}`.")
            return

        div_id = division["id"]
        current_season = division["season"]

        settings = await get_division_settings(pool, div_id)
        groups = await pool.fetch(
            "SELECT * FROM division_groups WHERE division_id = $1", div_id
        )
        groups_snapshot = [dict(g) for g in groups]

        await pool.execute(
            """
            INSERT INTO division_season_archive (division_id, season, settings_snapshot, groups_snapshot)
            VALUES ($1, $2, $3, $4)
            """,
            div_id, current_season,
            json.dumps(settings), json.dumps(groups_snapshot)
        )

        await pool.execute("DELETE FROM division_groups WHERE division_id = $1", div_id)
        await pool.execute("DELETE FROM division_participants WHERE division_id = $1", div_id)
        await pool.execute("DELETE FROM division_settings WHERE division_id = $1", div_id)

        new_season = str(int(current_season) + 1) if current_season.isdigit() else current_season + "_new"
        await pool.execute(
            "UPDATE divisions SET season = $1 WHERE id = $2",
            new_season, div_id
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="New Season Started",
                description=f"**{division['name']}** season `{current_season}` has been archived. Season `{new_season}` is now active.",
                color=discord.Color.gold()
            )
        )
