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


async def enablecog(interaction: discord.Interaction, server_id: str, cog: str):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    pool = await get_pool()

    result = await pool.execute(
        "DELETE FROM disabled_cogs WHERE server_id=$1 AND cog_name=$2",
        server_id, cog
    )
    if result == "DELETE 0":
        await interaction.response.send_message(
            f"❌ `{cog}` is already enabled for `{server_id}`.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🟢 Cog Enabled",
        color=0x2ecc71
    )
    embed.add_field(name="Server ID", value=f"`{server_id}`", inline=True)
    embed.add_field(name="Cog", value=f"`{cog}`", inline=True)
    await interaction.response.send_message(embed=embed)


def setup_choices(cmd):
    cmd = app_commands.describe(
        server_id="The server ID to enable the cog for",
        cog="The cog to enable"
    )(cmd)
    cmd = app_commands.choices(cog=[
        app_commands.Choice(name=c, value=c) for c in TOGGLEABLE_COGS
    ])(cmd)
    return cmd

enablecog = setup_choices(enablecog)
