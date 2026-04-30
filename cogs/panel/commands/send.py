import discord
from discord import app_commands
from database.db import get_pool
from cogs.division.utils import check_division_admin
import coc


class ClaimModal(discord.ui.Modal, title="Claim CoC Account"):
    tag = discord.ui.TextInput(
        label="Player Tag",
        placeholder="#ABC123",
        required=True
    )
    api = discord.ui.TextInput(
        label="API Token",
        placeholder="Your in-game API token",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        tag = self.tag.value.strip().upper()
        if not tag.startswith("#"):
            tag = "#" + tag

        pool = await get_pool()

        existing = await pool.fetchrow(
            "SELECT discord_id FROM acc_accounts WHERE tag = $1", tag
        )
        if existing:
            if existing["discord_id"] == interaction.user.id:
                embed = discord.Embed(
                    description="❌ You have already claimed this account.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    description="❌ This account is already claimed by another user.",
                    color=discord.Color.red()
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        coc_client = interaction.client.coc_client
        try:
            result = await coc_client.verify_player_token(tag, self.api.value.strip())
            if not result:
                embed = discord.Embed(
                    description="❌ Invalid API token. Please check your in-game settings.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        except coc.NotFound:
            embed = discord.Embed(
                description=f"❌ Player tag `{tag}` not found.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        except coc.ClashOfClansException as e:
            embed = discord.Embed(
                description=f"❌ CoC API error: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            player = await coc_client.get_player(tag)
        except coc.ClashOfClansException as e:
            embed = discord.Embed(
                description=f"❌ Could not fetch player data: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
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

        from utils.emojis import get_th_emoji
        th_emoji = get_th_emoji(th_level)
        embed = discord.Embed(
            title="✅ Account Linked",
            description=f"{th_emoji} **{ign}** (`{tag}`) has been linked to your account.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Claimed by {interaction.user.display_name}")
        await interaction.followup.send(embed=embed, ephemeral=True)


class ClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Claim Account",
        style=discord.ButtonStyle.primary,
        custom_id="panel:claim"
    )
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ClaimModal())


async def send(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not await check_division_admin(interaction):
        embed = discord.Embed(
            description="❌ You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(
        title="🎮 Claim Your CoC Account",
        description=(
            "Link your Clash of Clans account to your Discord profile.\n\n"
            "**How to get your API token:**\n"
            "1. Open Clash of Clans\n"
            "2. Go to **Settings → More Settings**\n"
            "3. Scroll down and tap **Show** under API Token\n\n"
            "Click the button below to get started!"
        ),
        color=discord.Color.blue()
    )

    await interaction.channel.send(embed=embed, view=ClaimView())
    await interaction.followup.send("✅ Panel sent!", ephemeral=True)
