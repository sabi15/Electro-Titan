import discord
from discord import ui
from database.db import get_pool
from cogs.league.utils import check_league_admin, get_league


FIELD_LABELS = {
    "description": "Description",
    "invite_link": "Server Invite Link",
    "ban_duration": "Ban Duration (days)",
    "code": "Code",
}

SETUP_OPTIONS = [
    discord.SelectOption(label="Description", value="description", emoji="📝"),
    discord.SelectOption(label="Server Invite Link", value="invite_link", emoji="🔗"),
    discord.SelectOption(label="Ban Duration (days)", value="ban_duration", emoji="⏱️"),
    discord.SelectOption(label="Code", value="code", emoji="🏷️"),
]


def build_embed(league_name: str, current: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"League Setup — {league_name}",
        color=discord.Color.blurple()
    )
    embed.add_field(
        name="📝 Description",
        value=current.get("description") or "*Not set*",
        inline=False
    )
    embed.add_field(
        name="🔗 Server Invite Link",
        value=current.get("invite_link") or "*Not set*",
        inline=False
    )
    embed.add_field(
        name="🏷️ Code",
        value=f"`{current.get('code')}`" if current.get("code") else "*Not set*",
        inline=False
    )
    embed.add_field(
        name="⏱️ Ban Duration",
        value=f"{current.get('ban_duration')} days" if current.get("ban_duration") else "*Not set*",
        inline=False
    )
    embed.set_footer(text="Select the fields you want to modify from the dropdown below.")
    return embed


class SetupModal(ui.Modal, title="League Setup"):
    def __init__(self, view: "SetupView", selected_fields: list[str]):
        super().__init__()
        self.setup_view = view
        self.selected_fields = selected_fields
        self.field_inputs = {}

        placeholders = {
            "description": "Enter league description",
            "invite_link": "Enter Discord invite URL",
            "ban_duration": "Enter number of days (e.g. 30)",
            "code": "Enter new league code (e.g. GBS-OL)",
        }

        for field in selected_fields:
            text_input = ui.TextInput(
                label=FIELD_LABELS[field],
                placeholder=placeholders[field],
                default=str(self.setup_view.current.get(field) or ""),
                required=True,
                max_length=500 if field == "description" else 100
            )
            self.field_inputs[field] = text_input
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()

        updates = {}
        for field, text_input in self.field_inputs.items():
            value = text_input.value.strip()
            if field == "ban_duration":
                if not value.isdigit():
                    await interaction.response.send_message(
                        "Ban duration must be a whole number.", ephemeral=False
                    )
                    return
                updates[field] = int(value)
            elif field == "code":
                updates[field] = value.upper()
            else:
                updates[field] = value

        set_clauses = ", ".join(
            f"{col} = ${i + 3}" for i, col in enumerate(updates.keys())
        )
        values = list(updates.values())

        await pool.execute(
            f"UPDATE leagues SET {set_clauses} WHERE guild_id = $1 AND code = $2",
            self.setup_view.guild_id, self.setup_view.league_code, *values
        )

        # Update local current state so next modal open shows new values
        self.setup_view.current.update(updates)
        if "code" in updates:
            self.setup_view.league_code = updates["code"]

        new_embed = build_embed(self.setup_view.league_name, self.setup_view.current)
        await interaction.response.edit_message(embed=new_embed, view=self.setup_view)


class SetupDropdown(ui.Select):
    def __init__(self, view: "SetupView"):
        self.setup_view = view
        super().__init__(
            placeholder="Select fields to edit...",
            min_values=1,
            max_values=4,
            options=SETUP_OPTIONS
        )

    async def callback(self, interaction: discord.Interaction):
        modal = SetupModal(self.setup_view, self.values)
        await interaction.response.send_modal(modal)


class SetupView(ui.View):
    def __init__(self, guild_id: int, league_code: str, league_name: str, current: dict):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.league_code = league_code
        self.league_name = league_name
        self.current = current
        self.message: discord.Message | None = None

        self.dropdown = SetupDropdown(self)
        self.add_item(self.dropdown)

    async def disable_all(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def on_timeout(self):
        await self.disable_all()

    @ui.button(label="Save & Close", style=discord.ButtonStyle.green, row=1)
    async def save_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.disable_all()
        await interaction.response.edit_message(
            content="✅ Setup saved and closed.",
            view=self
        )

    @ui.button(label="Cancel", style=discord.ButtonStyle.red, row=1)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.disable_all()
        await interaction.response.edit_message(
            content="❌ Setup cancelled.",
            embed=None,
            view=self
        )


async def league_setup(interaction: discord.Interaction, code: str):
    if not await check_league_admin(interaction):
        await interaction.response.send_message("You don't have permission to use this command.")
        return

    code = code.upper()
    league = await get_league(interaction.guild_id, code)
    if not league:
        await interaction.response.send_message(f"No league found with code `{code}`.")
        return

    current = dict(league)
    embed = build_embed(league['name'], current)
    view = SetupView(interaction.guild_id, code, league['name'], current)

    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()
