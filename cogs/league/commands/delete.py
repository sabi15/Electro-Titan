import discord
from database.db import get_pool
from cogs.league.utils import check_league_admin, get_league


async def league_delete(interaction: discord.Interaction, code: str):
    if not await check_league_admin(interaction):
        await interaction.response.send_message("You don't have permission to use this command.")
        return

    code = code.upper()
    league = await get_league(interaction.guild_id, code)
    if not league:
        await interaction.response.send_message(f"No league found with code `{code}`.")
        return

    pool = await get_pool()
    await pool.execute(
        "DELETE FROM leagues WHERE guild_id = $1 AND code = $2",
        interaction.guild_id, code
    )

    embed = discord.Embed(
        title="League Deleted",
        description=f"**{league['name']}** (`{code}`) has been deleted.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)
