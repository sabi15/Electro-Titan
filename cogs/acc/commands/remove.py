import discord
from discord import app_commands
from database.db import get_pool
from cogs.acc.utils import maybe_send_invite


@app_commands.describe(tag="The CoC player tag to remove (e.g. #ABC123)")
async def remove(interaction: discord.Interaction, tag: str):
    await interaction.response.defer()

    if not tag.startswith("#"):
        tag = "#" + tag
    tag = tag.upper()

    pool = await get_pool()

    row = await pool.fetchrow(
        "SELECT discord_id, ign, th_level FROM acc_accounts WHERE tag = $1",
        tag
    )

    if not row:
        embed = discord.Embed(
            description=f"❌ No account found for tag `{tag}`.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    if row["discord_id"] != interaction.user.id:
        embed = discord.Embed(
            description="❌ You can only remove accounts that you have claimed.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM acc_accounts WHERE tag = $1", tag
            )
            await conn.execute(
                """
                INSERT INTO acc_history (discord_id, tag, ign, th_level, action)
                VALUES ($1, $2, $3, $4, 'removed')
                """,
                interaction.user.id, tag, row["ign"], row["th_level"]
            )

    embed = discord.Embed(
        title="Account Unlinked",
        description=f"✅ **{row['ign']}** (`{tag}`) has been removed from your linked accounts.",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Removed by {interaction.user.display_name}")
    await interaction.followup.send(embed=embed)

    invite = await maybe_send_invite(interaction.user.id, interaction.guild_id)
    if invite:
        await interaction.followup.send(invite)
