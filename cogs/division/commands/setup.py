import discord
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
    lines = []
    for key in SETTINGS_PAGES[page]:
        val = settings.get(key, "_not set_")
        lines.append(f"`{key}`: {val}")
    embed.description = "\n".join(lines)
    embed.set_footer(text=f"Page {page + 1} of {len(SETTINGS_PAGES)} — Select a setting to configure it.")
    return embed


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
        self._rebuild()

    def _rebuild(self):
        self.clear_items()

        select = discord.ui.Select(
            placeholder="Select a setting to configure...",
            options=[discord.SelectOption(label=k, value=k) for k in SETTINGS_PAGES[self.page]],
            min_values=1,
            max_values=1
        )

        async def select_callback(interaction: discord.Interaction):
            key = select.values[0]
            current_val = self.settings.get(key, "")
            modal = SettingModal(key, current_val, self.division_id, self.division_name, self)
            await interaction.response.send_modal(modal)

        select.callback = select_callback
        self.add_item(select)

        first = discord.ui.Button(label="⏮", style=discord.ButtonStyle.secondary, disabled=self.page == 0)
        prev = discord.ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.page == 0)
        next_ = discord.ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.page == len(SETTINGS_PAGES) - 1)
        last = discord.ui.Button(label="⏭", style=discord.ButtonStyle.secondary, disabled=self.page == len(SETTINGS_PAGES) - 1)
        cancel = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)

        async def first_cb(interaction: discord.Interaction):
            self.page = 0
            self._rebuild()
            await interaction.response.edit_message(embed=build_setup_embed(self.division_name, self.settings, self.page), view=self)

        async def prev_cb(interaction: discord.Interaction):
            self.page = max(0, self.page - 1)
            self._rebuild()
            await interaction.response.edit_message(embed=build_setup_embed(self.division_name, self.settings, self.page), view=self)

        async def next_cb(interaction: discord.Interaction):
            self.page = min(len(SETTINGS_PAGES) - 1, self.page + 1)
            self._rebuild()
            await interaction.response.edit_message(embed=build_setup_embed(self.division_name, self.settings, self.page), view=self)

        async def last_cb(interaction: discord.Interaction):
            self.page = len(SETTINGS_PAGES) - 1
            self._rebuild()
            await interaction.response.edit_message(embed=build_setup_embed(self.division_name, self.settings, self.page), view=self)

        async def cancel_cb(interaction: discord.Interaction):
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(content="Setup cancelled.", embed=None, view=self)

        first.callback = first_cb
        prev.callback = prev_cb
        next_.callback = next_cb
        last.callback = last_cb
        cancel.callback = cancel_cb

        self.add_item(first)
        self.add_item(prev)
        self.add_item(next_)
        self.add_item(last)
        self.add_item(cancel)


async def division_setup(interaction: discord.Interaction, division: str):
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
    view = SetupView(dict(div), settings)
    embed = build_setup_embed(div["name"], settings, 0)
    await interaction.response.send_message(embed=embed, view=view)
