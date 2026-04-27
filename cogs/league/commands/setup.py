import discord
from discord import ui
from db import get_pool
from cogs.league.utils import check_league_admin, get_league


SETUP_OPTIONS = [
    discord.SelectOption(label="Description", value="description"),
    discord.SelectOption(label="Server Invite Link", value="invite_link"),
    discord.SelectOption(label="Ban Duration (days)", value="ban_duration"),
    discord.SelectOption(label="Code", value="code"),
]


class SetupModal(ui.Modal, title="League Setup"):
    def __init__(self, guild_id: int, league_code: str, selected_fields: list[str]):
        super().__init__()
        self.guild_id = guild_id
        self.league_code = league_code
        self.selected_fields = selected_fields
        self.field_inputs = {}

        labels = {
            "description": ("Description", "Enter league description", ui.TextInput),
            "invite_link": ("Server Invite Link", "Enter Discord invite URL", ui.TextInput),
            "ban_duration": ("Ban Duration", "Enter number of days (e.g. 30)", ui.TextInput),
            "code": ("Code", "Enter new league code (e.g. GBS-OL)", ui.TextInput),
        }

        for field in selected_fields:
            label, placeholder, InputClass = labels[field]
            text_input = InputClass(
                label=label,
                placeholder=placeholder,
                required=True,
                max_length=200 if field == "description" else 100
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
                    await interaction.response.send_message("Ban duration must be a number.")
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
            self.guild_id, self.league_code, *values
        )

        new_code = updates.get("code", self.league_code)
        embed = discord.Embed(
            title="League Updated",
            description=f"Settings for `{new_code}` have been saved.",
            color=discord.Color.green()
        )
        for field, value in updates.items():
            embed.add_field(name=field.replace("_", " ").title(), value=str(value), inline=False)

        await interaction.response.send_message(embed=embed)


class SetupDropdown(ui.Select):
    def __init__(self, guild_id: int, league_code: str, current: dict):
        self.guild_id = guild_id
        self.league_code = league_code
        self.current = current
        super().__init__(
            placeholder="Select fields to edit...",
            min_values=1,
            max_values=4,
            options=SETUP_OPTIONS
        )

    async def callback(self, interaction: discord.Interaction):
        modal = SetupModal(self.guild_id, self.league_code, self.values)
        await interaction.response.send_modal(modal)


class SetupView(ui.View):
    def __init__(self, guild_id: int, league_code: str, current: dict):
        super().__init__(timeout=120)
        self.add_item(SetupDropdown(guild_id, league_code, current))


async def league_setup(interaction: discord.Interaction, code: str):
    if not await check_league_admin(interaction):
        await interaction.response.send_message("You don't have permission to use this command.")
        return

    code = code.upper()
    league = await get_league(interaction.guild_id, code)
    if not league:
        await interaction.response.send_message(f"No league found with code `{code}`.")
        return

    embed = discord.Embed(
        title=f"Setup — {league['name']} ({code})",
        description="Select one or more fields from the dropdown below to edit them.",
        color=discord.Color.blurple()
    )
    embed.add_field(name="1. Description", value=league['description'] or "*Not set*", inline=False)
    embed.add_field(name="2. Server Invite Link", value=league['invite_link'] or "*Not set*", inline=False)
    embed.add_field(name="3. Ban Duration", value=f"{league['ban_duration']} days" if league['ban_duration'] else "*Not set*", inline=False)
    embed.add_field(name="4. Code", value=f"`{league['code']}`", inline=False)

    view = SetupView(interaction.guild_id, code, dict(league))
    await interaction.response.send_message(embed=embed, view=view)
