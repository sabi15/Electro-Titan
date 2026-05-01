import discord
from discord import ui
from database.db import get_pool
from cogs.division.utils import (
    get_division_by_code, get_division_settings,
    SETTINGS_PAGES, SETTING_DEFAULTS
)

PAGE_NAMES = ["Roster & Players", "Applications & Transactions", "Match & Stream"]


def build_showsetup_embed(division_name: str, settings: dict, page: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"Setup — {division_name}",
        description=f"📋 **{PAGE_NAMES[page]}**",
        color=discord.Color.blurple()
    )

    lines = []
    for key in SETTINGS_PAGES[page]:
        val = settings.get(key) or SETTING_DEFAULTS.get(key)
        if val:
            display = val if len(val) <= 80 else val[:77] + "..."
            lines.append(f"`{key}`\n{display}")
        else:
            lines.append(f"`{key}`\n_not set_")

    embed.description += "\n\n" + "\n\n".join(lines)
    embed.set_footer(text=f"Page {page + 1} of {len(SETTINGS_PAGES)}")
    return embed


class ShowSetupView(ui.View):
    def __init__(self, division: dict, settings: dict):
        super().__init__(timeout=120)
        self.division_name = division["name"]
        self.settings = settings
        self.page = 0
        self.message: discord.Message | None = None
        self._rebuild()

    def _rebuild(self):
        self.clear_items()

        first = ui.Button(label="⏮", style=discord.ButtonStyle.secondary, disabled=self.page == 0, row=0)
        prev = ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.page == 0, row=0)
        next_ = ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.page == len(SETTINGS_PAGES) - 1, row=0)
        last = ui.Button(label="⏭", style=discord.ButtonStyle.secondary, disabled=self.page == len(SETTINGS_PAGES) - 1, row=0)
        close = ui.Button(label="Close", style=discord.ButtonStyle.danger, row=0)

        async def first_cb(interaction: discord.Interaction):
            self.page = 0
            self._rebuild()
            await interaction.response.edit_message(
                embed=build_showsetup_embed(self.division_name, self.settings, self.page),
                view=self
            )

        async def prev_cb(interaction: discord.Interaction):
            self.page = max(0, self.page - 1)
            self._rebuild()
            await interaction.response.edit_message(
                embed=build_showsetup_embed(self.division_name, self.settings, self.page),
                view=self
            )

        async def next_cb(interaction: discord.Interaction):
            self.page = min(len(SETTINGS_PAGES) - 1, self.page + 1)
            self._rebuild()
            await interaction.response.edit_message(
                embed=build_showsetup_embed(self.division_name, self.settings, self.page),
                view=self
            )

        async def last_cb(interaction: discord.Interaction):
            self.page = len(SETTINGS_PAGES) - 1
            self._rebuild()
            await interaction.response.edit_message(
                embed=build_showsetup_embed(self.division_name, self.settings, self.page),
                view=self
            )

        async def close_cb(interaction: discord.Interaction):
            await self.disable_all()
            await interaction.response.edit_message(view=self)

        first.callback = first_cb
        prev.callback = prev_cb
        next_.callback = next_cb
        last.callback = last_cb
        close.callback = close_cb

        self.add_item(first)
        self.add_item(prev)
        self.add_item(next_)
        self.add_item(last)
        self.add_item(close)

    async def disable_all(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def on_timeout(self):
        await self.disable_all()


async def division_showsetup(interaction: discord.Interaction, division: str):
    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    div = await get_division_by_code(pool, guild_id, division)
    if not div:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"No division found with code `{division.upper()}`.",
                color=discord.Color.red()
            )
        )
        return

    settings = await get_division_settings(pool, div["id"])
    view = ShowSetupView(dict(div), settings)
    embed = build_showsetup_embed(div["name"], settings, 0)

    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()
