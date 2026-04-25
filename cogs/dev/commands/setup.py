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

async def build_embed(bot, guild, pool):
    gid = str(guild.id)

    disabled = await pool.fetch(
        "SELECT cog_name FROM disabled_cogs WHERE server_id=$1", gid
    )
    disabled_names = [r["cog_name"] for r in disabled]
    enabled_names = [c for c in TOGGLEABLE_COGS if c not in disabled_names]

    whitelisted = await pool.fetchrow(
        "SELECT whitelisted FROM whitelisted_servers WHERE server_id=$1", gid
    )
    status = "✅ Whitelisted" if whitelisted and whitelisted["whitelisted"] else "🚫 Not Whitelisted"

    embed = discord.Embed(
        title=f"⚙️ {guild.name}",
        color=0x2b2d31
    )
    embed.add_field(name="Server ID", value=f"`{gid}`", inline=False)
    embed.add_field(name="Whitelist Status", value=status, inline=False)
    embed.add_field(
        name="✅ Enabled Cogs",
        value=", ".join(f"`{c}`" for c in enabled_names) or "None",
        inline=False
    )
    embed.add_field(
        name="🔴 Disabled Cogs",
        value=", ".join(f"`{c}`" for c in disabled_names) or "None",
        inline=False
    )
    return embed


class SetupPaginator(discord.ui.View):
    def __init__(self, bot, guilds, pool):
        super().__init__(timeout=60)
        self.bot = bot
        self.guilds = guilds
        self.pool = pool
        self.page = 0

    async def get_embed(self):
        guild = self.guilds[self.page]
        embed = await build_embed(self.bot, guild, self.pool)
        embed.set_footer(text=f"Server {self.page + 1} of {len(self.guilds)}")
        return embed

    def update_buttons(self):
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page == len(self.guilds) - 1

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=await self.get_embed(), view=self
        )

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=await self.get_embed(), view=self
        )


async def setup(interaction: discord.Interaction):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.")
        return

    await interaction.response.defer()
    pool = await get_pool()
    guilds = interaction.client.guilds

    if not guilds:
        await interaction.followup.send("❌ Bot is not in any servers.")
        return

    view = SetupPaginator(interaction.client, guilds, pool)
    view.update_buttons()
    embed = await view.get_embed()
    await interaction.followup.send(embed=embed, view=view)
