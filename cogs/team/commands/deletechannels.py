import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import is_division_admin


async def team_deletechannels(interaction: discord.Interaction, division: str):
    if not await check_access(interaction, "team"):
        return
    await interaction.response.defer()
    pool = await get_pool()
    gid = str(interaction.guild_id)
    division = division.strip().upper()

    if not await is_division_admin(interaction):
        await interaction.followup.send(embed=discord.Embed(
            description="❌ Requires DIVISION_ADMIN.",
            color=0xe74c3c
        ))
        return

    apps = await pool.fetch(
        "SELECT channel_id FROM applications WHERE guild_id=$1 AND division_code=$2",
        gid, division
    )
    if not apps:
        await interaction.followup.send(embed=discord.Embed(
            description=f"❌ No application channels found for **{division}**.",
            color=0xe74c3c
        ))
        return

    deleted_channels = 0
    deleted_categories = 0
    category_names = set()

    for row in apps:
        channel = interaction.guild.get_channel(int(row['channel_id']))
        if channel:
            if channel.category:
                category_names.add(channel.category.name)
            try:
                await channel.delete()
                deleted_channels += 1
            except Exception:
                pass

    # Delete empty App categories for this division
    for cat in interaction.guild.categories:
        if cat.name.startswith(f"Apps-{division}") and len(cat.channels) == 0:
            try:
                await cat.delete()
                deleted_categories += 1
            except Exception:
                pass

    await interaction.followup.send(embed=discord.Embed(
        description=(
            f"✅ Deleted **{deleted_channels}** application channel(s) "
            f"and **{deleted_categories}** empty category(ies) for **{division}**."
        ),
        color=0x2ecc71
    ))
