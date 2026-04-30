import discord
from database.db import get_pool
from cogs.division.utils import get_division_by_code, get_division_settings, SETTINGS_PAGES


async def division_showsetup(interaction: discord.Interaction, division: str):
    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    div = await get_division_by_code(pool, guild_id, division)
    if not div:
        await interaction.response.send_message(f"No division found with code `{division.upper()}`.")
        return

    settings = await get_division_settings(pool, div["id"])

    if not settings:
        await interaction.response.send_message(f"No settings configured for **{div['name']}** yet.")
        return

    embed = discord.Embed(
        title=f"Setup — {div['name']}",
        color=discord.Color.blurple()
    )

    for i, page_keys in enumerate(SETTINGS_PAGES):
        lines = []
        for key in page_keys:
            val = settings.get(key)
            if val:
                lines.append(f"`{key}`: {val}")
        if lines:
            embed.add_field(
                name=f"Page {i + 1}",
                value="\n".join(lines),
                inline=False
            )

    if not embed.fields:
        await interaction.response.send_message(f"No settings configured for **{div['name']}** yet.")
        return

    await interaction.response.send_message(embed=embed)
