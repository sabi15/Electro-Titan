import discord
from discord.ext import commands
from discord import app_commands
from database.db import get_pool
from cogs.division.utils import (
    check_division_admin, get_division_by_code,
    get_division_settings, upsert_setting, SETTINGS_PAGES
)

def build_setup_embed(division_name: str, settings: dict, page: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"Division Setup — {division_name}",
        color=discord.Color.blurple()
    )
    current_page_keys = SETTINGS_PAGES[page]
    lines = []
    for key in current_page_keys:
        val = settings.get(key, "_not set_")
        lines.append(f"`{key}`: {val}")
    embed.description = "\n".join(lines)
    embed.set_footer(text=f"Page {page + 1} of {len(SETTINGS_PAGES)} — Select a setting to configure it.")
    return embed

def build_dropdown(page: int) -> discord.ui.Select:
    options = [
        discord.SelectOption(label=key, value=key)
        for key in SETTINGS_PAGES[page]
    ]
    select = discord.ui.Select(
        placeholder="Select a setting to configure...",
        options=options,
        min_values=1,
        max_values=1
    )
    return select

class SettingModal(discord.ui.Modal):
    def __init__(self, key: str, current_value: str, division_id: int, division_name: str, view: "SetupView"):
        super().__init__(title=f"Configure: {key}")
        self.key = key
        self.division_id = division_id
        self.view_ref = view
        self.value_input = discord.ui.TextInput(
            label=key,
            default=current_value if current_value != "_not set_" else "",
            required=False,
            max_length=500
        )
        self.add_item(self.value_input)

    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        await upsert_setting(pool, self.division_id, self.key, self.value_input.value)
        self.view_ref.settings[self.key] = self.value_input.value
        embed = build_setup_embed(self.view_ref.division_name, self.view_ref.settings, self.view_ref.page)
        await interaction.response.edit_message(embed=embed, view=self.view_ref)

class SetupView(discord.ui.View):
    def __init__(self, division: dict, settings: dict):
        super().__init__(timeout=180)
        self.division = division
        self.division_name = division["name"]
        self.division_id = division["id"]
        self.settings = settings
        self.page = 0
        self._add_components()

    def _add_components(self):
        self.clear_items()

        select = build_dropdown(self.page)

        async def select_callback(interaction: discord.Interaction):
            key = select.values[0]
            current_val = self.settings.get(key, "")
            modal = SettingModal(key, current_val, self.division_id, self.division_name, self)
            await interaction.response.send_modal(modal)

        select.callback = select_callback
        self.add_item(select)

        first_btn = discord.ui.Button(label="⏮", style=discord.ButtonStyle.secondary, disabled=self.page == 0)
        prev_btn = discord.ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.page == 0)
        next_btn = discord.ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.page == len(SETTINGS_PAGES) - 1)
        last_btn = discord.ui.Button(label="⏭", style=discord.ButtonStyle.secondary, disabled=self.page == len(SETTINGS_PAGES) - 1)
        cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)

        async def first_callback(interaction: discord.Interaction):
            self.page = 0
            self._add_components()
            await interaction.response.edit_message(embed=build_setup_embed(self.division_name, self.settings, self.page), view=self)

        async def prev_callback(interaction: discord.Interaction):
            self.page = max(0, self.page - 1)
            self._add_components()
            await interaction.response.edit_message(embed=build_setup_embed(self.division_name, self.settings, self.page), view=self)

        async def next_callback(interaction: discord.Interaction):
            self.page = min(len(SETTINGS_PAGES) - 1, self.page + 1)
            self._add_components()
            await interaction.response.edit_message(embed=build_setup_embed(self.division_name, self.settings, self.page), view=self)

        async def last_callback(interaction: discord.Interaction):
            self.page = len(SETTINGS_PAGES) - 1
            self._add_components()
            await interaction.response.edit_message(embed=build_setup_embed(self.division_name, self.settings, self.page), view=self)

        async def cancel_callback(interaction: discord.Interaction):
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(content="Setup cancelled.", view=self)

        first_btn.callback = first_callback
        prev_btn.callback = prev_callback
        next_btn.callback = next_callback
        last_btn.callback = last_callback
        cancel_btn.callback = cancel_callback

        self.add_item(first_btn)
        self.add_item(prev_btn)
        self.add_item(next_btn)
        self.add_item(last_btn)
        self.add_item(cancel_btn)

class DivisionSetup(commands.Cog):
    @app_commands.command(name="division-setup", description="Configure settings for a division.")
    @app_commands.describe(division="Division code")
    async def division_setup(self, interaction: discord.Interaction, division: str):
        if not await check_division_admin(interaction):
            await interaction.response.send_message("You don't have permission to do this.")
            return

        guild_id = str(interaction.guild_id)
        pool = await get_pool()

        div = await get_division_by_code(pool, guild_id, division)
        if not div:
            await interaction.response.send_message(f"No division found with code `{division.upper()}`.")
            return

        settings = await get_division_settings(pool, div["id"])
        view = SetupView(div, settings)
        embed = build_setup_embed(div["name"], settings, 0)
        await interaction.response.send_message(embed=embed, view=view)
