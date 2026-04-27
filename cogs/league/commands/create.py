import discord
from discord import app_commands
from db import get_pool
from cogs.league.utils import check_league_admin


async def league_create(interaction: discord.Interaction, name: str, code: str):
    if not await check_league_admin(interaction):
        await interaction.response.send_message("You don't have permission to use this command.")
        return

    code = code.upper()
    pool = await get_pool()

    existing = await pool.fetchrow(
        "SELECT 1 FROM leagues WHERE guild_id = $1 AND code = $2",
        interaction.guild_id, code
    )
    if existing:
        await interaction.response.send_message(f"A league with code `{code}` already exists in this server.")
        return

    await pool.execute(
        """
        INSERT INTO leagues (guild_id, name, code)
        VALUES ($1, $2, $3)
        """,
        interaction.guild_id, name, code
    )

    embed = discord.Embed(
        title="League Created",
        color=discord.Color.green()
    )
    embed.add_field(name="Name", value=name, inline=True)
    embed.add_field(name="Code", value=code, inline=True)
    embed.set_footer(text="Use /league setup to configure description, invite link, and ban duration.")

    await interaction.response.send_message(embed=embed)
