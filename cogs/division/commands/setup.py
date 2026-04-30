import discord
from discord import ui
from database.db import get_pool
from cogs.division.utils import (
    check_division_admin, get_division_by_code,
    get_division_settings, upsert_setting,
    SETTINGS_PAGES, SETTING_DEFAULTS, validate_setting
)


def build_embed(division_name: str, settings: dict, page: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"Division Setup — {division_name}",
        color=discord.Color.blurple()
    )
    lines = []
    for i, key in enumerate(SETTINGS_PAGES[page], start=1):
        current = settings.get(key) or SETTING_DEFAULTS.get(key, "_not set_")
        lines.append(f"`{key}` — {current}")
    embed.description = "\n".join(lines)
    embed.set_footer(text=f"Page {page + 1} of {len(SETTINGS_PAGES)} — Select a setting to configure it.")
    return embed


class SettingModal(ui.Modal):
    def __init__(self, keys: list[str], current: dict, division_id: int, division_name: str, view: "SetupView"):
        super().__init__(title="Division Setup")
        self.keys = keys
        self.division_id = division_id
        self.view_ref = view
        self.field_inputs = {}

        for key in keys[:5]:  # Discord modal max 5 inputs
            default = current.get(key) or SETTING_DEFAULTS.get(key, "")
            text_input = ui.TextInput(
                label=key,
                default=str(default),
                required=False,
                max_length=1000
            )
            self.field_inputs[key] = text_input
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        errors = []
        updates = {}

        for key, text_input in self.field_inputs.items():
            value = text_input.value.strip()
            if not value:
                continue
            error = validate_setting(key, value)
            if error:
                errors.append(error)
            else:
                updates[key] = value

        if errors:
            error_embed = discord.Embed(
                title="Setup Errors",
                description="\n\n".join(errors),
                color=discord.Color.red()
            )
            await interaction.response.defer()
            await interaction.followup.send(embed=error_embed)
            return

        for key, value in updates.items():
            await upsert_setting(pool, self.division_id, key, value)
            self.view_ref.settings[key] = value

        if updates:
            changes_embed = discord.Embed(
                title="Settings Updated",
                description="\n".join(f"✅ **{k}** → `{v}`" for k, v in updates.items()),
                color=discord.Color.green()
            )
            new_embed = build_embed(self.view_ref.division_name, self.view_ref.settings, self.view_ref.page)
            await interaction.response.edit_message(embed=new_embed, view=self.view_ref)
            await interaction.followup.send(embed=changes_embed)
        else:
            await interaction.response.defer()


class SetupDropdown(ui.Select):
    def __init__(self, view: "SetupView"):
        self.setup_view = view
        options = [
            discord.SelectOption(label=key, value=key)
            for key in SETTINGS_PAGES[view.page]
        ]
        super().__init__(
            placeholder="Select settings to configure...",
            min_values=1,
            max_values=min(5, len(SETTINGS_PAGES[view.page])),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_keys = self.values
        modal = SettingModal(
            selected_keys,
            self.setup_view.settings,
            self.setup_view.division_id,
            self.setup_view.division_name,
            self.setup_view
        )
        await interaction.response.send_modal(modal)


class SetupView(ui.View):
    def __init__(self, division: dict, settings: dict):
        super().__init__(timeout=180)
        self.division = division
        self.division_name = division["name"]
        self.division_id = division["id"]
        self.settings = settings
        self.page = 0
        self.message: discord.Message | None = None
        self._rebuild()

    def _rebuild(self):
        self.clear_items()
        self.add_item(SetupDropdown(self))

        first = ui.Button(label="⏮", style=discord.ButtonStyle.secondary, disabled=self.page == 0, row=1)
        prev = ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.page == 0, row=1)
        next_ = ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.page == len(SETTINGS_PAGES) - 1, row=1)
        last = ui.Button(label="⏭", style=discord.ButtonStyle.secondary, disabled=self.page == len(SETTINGS_PAGES) - 1, row=1)
        cancel = ui.Button(label="Cancel", style=discord.ButtonStyle.danger, row=1)

        async def first_cb(interaction: discord.Interaction):
            self.page = 0
            self._rebuild()
            await interaction.response.edit_message(embed=build_embed(self.division_name, self.settings, self.page), view=self)

        async def prev_cb(interaction: discord.Interaction):
            self.page = max(0, self.page - 1)
            self._rebuild()
            await interaction.response.edit_message(embed=build_embed(self.division_name, self.settings, self.page), view=self)

        async def next_cb(interaction: discord.Interaction):
            self.page = min(len(SETTINGS_PAGES) - 1, self.page + 1)
            self._rebuild()
            await interaction.response.edit_message(embed=build_embed(self.division_name, self.settings, self.page), view=self)

        async def last_cb(interaction: discord.Interaction):
            self.page = len(SETTINGS_PAGES) - 1
            self._rebuild()
            await interaction.response.edit_message(embed=build_embed(self.division_name, self.settings, self.page), view=self)

        async def cancel_cb(interaction: discord.Interaction):
            await self.disable_all()
            await interaction.response.edit_message(
                content="❌ Setup cancelled.",
                embed=None,
                view=self
            )

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

    async def disable_all(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def on_timeout(self):
        await self.disable_all()


async def division_setup(interaction: discord.Interaction, division: str):
    if not await check_division_admin(interaction):
        await interaction.response.send_message(
            embed=discord.Embed(description="You don't have permission to do this.", color=discord.Color.red())
        )
        return

    guild_id = str(interaction.guild_id)
    pool = await get_pool()

    div = await get_division_by_code(pool, guild_id, division)
    if not div:
        await interaction.response.send_message(
            embed=discord.Embed(description=f"No division found with code `{division.upper()}`.", color=discord.Color.red())
        )
        return

    settings = await get_division_settings(pool, div["id"])
    view = SetupView(dict(div), settings)
    embed = build_embed(div["name"], settings, 0)

    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()
