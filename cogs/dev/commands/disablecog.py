import discord
from discord import app_commands
from database.db import get_pool
from config import BOT_DEV_ID

TOGGLEABLE_COGS = [
    "division", "export", "feed", "fp",
    "league", "match", "banner",
    "schedule", "team", "transaction",
    "blist", "panel"
]


async def disablecog(interaction: discord.Interaction, server_id: str, cog: str):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    pool = await get_pool()

    existing = await pool.fetchrow(
        "SELECT 1 FROM disabled_cogs WHERE server_id=$1 AND cog_name=$2",
        server_id, cog
    )
    if existing:
        await interaction.response.send_message(
            f"❌ `{cog}` is already disabled for `{server_id}`.",
            ephemeral=True
        )
        return

    await pool.execute(
        "INSERT INTO disabled_cogs (server_id, cog_name) VALUES ($1, $2)",
        server_id, cog
    )

    embed = discord.Embed(
        title="🔴 Cog Disabled",
        color=0xe74c3c
    )
    embed.add_field(name="Server ID", value=f"`{server_id}`", inline=True)
    embed.add_field(name="Cog", value=f"`{cog}`", inline=True)
    await interaction.response.send_message(embed=embed)


def setup_choices(cmd):
    cmd = app_commands.describe(
        server_id="The server ID to disable the cog for",
        cog="The cog to disable"
    )(cmd)
    cmd = app_commands.choices(cog=[
        app_commands.Choice(name=c, value=c) for c in TOGGLEABLE_COGS
    ])(cmd)
    return cmd

disablecog = setup_choices(disablecog)
