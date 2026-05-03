import discord
from discord import app_commands
from database.db import get_pool
from utils.emojis import get_th_emoji
from cogs.acc.utils import maybe_send_invite
from utils.emojis import E_CORRECT, E_WRONG, E_WARN
import coc


@app_commands.describe(
    tag="Your Clash of Clans player tag from your profile (e.g. #ABC123)",
    api="Your API token from in game settings"
)
async def add(interaction: discord.Interaction, tag: str, api: str):
    await interaction.response.defer()

    if not tag.startswith("#"):
        tag = "#" + tag
    tag = tag.upper()

    pool = await get_pool()

    existing = await pool.fetchrow(
        "SELECT discord_id FROM acc_accounts WHERE tag = $1", tag
    )
    if existing:
        if existing["discord_id"] == interaction.user.id:
            embed = discord.Embed(
                description=f"{E_WRONG} You are already linked with this account.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                description=f"{E_WRONG} This account is already linked with another user.",
                color=discord.Color.red()
            )
        await interaction.followup.send(embed=embed)
        return

    coc_client = interaction.client.coc_client
    try:
        result = await coc_client.verify_player_token(tag, api)
        if not result:
            embed = discord.Embed(
                description=f"{E_WRONG} Invalid API token. Please check your ingame settings and try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
    except coc.NotFound:
        embed = discord.Embed(
            description=f"{E_WRONG} Player tag `{tag}` not found.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    except coc.ClashOfClansException as e:
        embed = discord.Embed(
            description=f"{E_WRONG} CoC API error: {e}",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    try:
        player = await coc_client.get_player(tag)
    except coc.ClashOfClansException as e:
        embed = discord.Embed(
            description=f"{E_WRONG} Could not fetch player data: {e}",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    ign = player.name
    th_level = player.town_hall

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO acc_accounts (discord_id, tag, ign, th_level)
                VALUES ($1, $2, $3, $4)
                """,
                interaction.user.id, tag, ign, th_level
            )
            await conn.execute(
                """
                INSERT INTO acc_history (discord_id, tag, ign, th_level, action)
                VALUES ($1, $2, $3, $4, 'claimed')
                """,
                interaction.user.id, tag, ign, th_level
            )

    th_emoji = get_th_emoji(th_level)
    embed = discord.Embed(
        title="Account Linked",
        description=f"{th_emoji} **{ign}** (`{tag}`) has been linked to {interaction.user.mention}.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Claimed by {interaction.user.display_name}")
    await interaction.followup.send(embed=embed)

    invite = await maybe_send_invite(interaction.user.id, interaction.guild_id)
    if invite:
        await interaction.followup.send(invite)
