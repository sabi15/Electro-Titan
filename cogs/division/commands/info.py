import discord
from discord.ext import commands
from discord import app_commands
from database.db import get_pool
from cogs.division.utils import get_division_by_code, get_division_settings

class DivisionInfo(commands.Cog):
    @app_commands.command(name="division-info", description="View details of a division.")
    @app_commands.describe(code="The division code")
    async def division_info(self, interaction: discord.Interaction, code: str):
        guild_id = str(interaction.guild_id)
        pool = await get_pool()

        division = await get_division_by_code(pool, guild_id, code)
        if not division:
            await interaction.response.send_message(f"No division found with code `{code.upper()}`.")
            return

        settings = await get_division_settings(pool, division["id"])
        color = discord.Color.green() if division["status"] == "active" else discord.Color.red()

        embed = discord.Embed(title=division["name"], color=color)
        embed.add_field(name="Code", value=division["code"], inline=True)
        embed.add_field(name="League", value=division["league_code"], inline=True)
        embed.add_field(name="Season", value=division["season"], inline=True)
        embed.add_field(name="Status", value=division["status"].capitalize(), inline=True)

        if division["rep_role_id"]:
            embed.add_field(name="Rep Role", value=f"<@&{division['rep_role_id']}>", inline=True)
        if division["transaction_log_channel_id"]:
            embed.add_field(name="Transaction Log", value=f"<#{division['transaction_log_channel_id']}>", inline=True)
        if division["logo_url"]:
            embed.set_thumbnail(url=division["logo_url"])

        if settings:
            preview = "\n".join(f"`{k}`: {v}" for k, v in list(settings.items())[:10])
            if len(settings) > 10:
                preview += f"\n_...and {len(settings) - 10} more settings_"
            embed.add_field(name="Settings", value=preview, inline=False)

        await interaction.response.send_message(embed=embed)
