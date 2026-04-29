import discord
from discord.ext import commands
from discord import app_commands
from database.db import get_pool
from cogs.division.utils import check_division_admin

class DivisionCreate(commands.Cog):
    @app_commands.command(name="division-create", description="Create a new division.")
    @app_commands.describe(
        division_name="Display name of the division",
        league_code="Code of the league this division belongs to",
        season="Starting season (e.g. 1)",
        transaction_log_channel="Channel for transaction logs",
        rep_role="Role assigned to team reps/participants"
    )
    async def division_create(
        self,
        interaction: discord.Interaction,
        division_name: str,
        league_code: str,
        season: str,
        transaction_log_channel: discord.TextChannel,
        rep_role: discord.Role
    ):
        if not await check_division_admin(interaction):
            await interaction.response.send_message("You don't have permission to create divisions.")
            return

        guild_id = str(interaction.guild_id)
        pool = await get_pool()

        league = await pool.fetchrow(
            "SELECT 1 FROM leagues WHERE guild_id = $1 AND code = $2",
            int(guild_id), league_code.upper()
        )
        if not league:
            await interaction.response.send_message(f"No league found with code `{league_code.upper()}`.")
            return

        code = division_name.upper().replace(" ", "_")

        existing = await pool.fetchrow(
            "SELECT 1 FROM divisions WHERE guild_id = $1 AND code = $2",
            guild_id, code
        )
        if existing:
            await interaction.response.send_message(f"A division with code `{code}` already exists.")
            return

        await pool.execute(
            """
            INSERT INTO divisions (guild_id, league_code, name, code, season, transaction_log_channel_id, rep_role_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            guild_id, league_code.upper(), division_name, code,
            season, str(transaction_log_channel.id), str(rep_role.id)
        )

        embed = discord.Embed(
            title="Division Created",
            color=discord.Color.green()
        )
        embed.add_field(name="Name", value=division_name, inline=True)
        embed.add_field(name="Code", value=code, inline=True)
        embed.add_field(name="League", value=league_code.upper(), inline=True)
        embed.add_field(name="Season", value=season, inline=True)
        embed.add_field(name="Transaction Log", value=transaction_log_channel.mention, inline=True)
        embed.add_field(name="Rep Role", value=rep_role.mention, inline=True)

        await interaction.response.send_message(embed=embed)
