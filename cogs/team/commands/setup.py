import discord
from discord import ui
from database.db import get_pool
from cogs.team.utils import is_division_admin, get_division_by_code
from utils.helpers import normalize_tag
import coc


SETUP_FIELDS = [
    "team_name",
    "team_code",
    "language",
    "timezone",
    "rep1",
    "rep2",
    "main_clan",
    "secondary_clan",
]


class TeamSettingModal(ui.Modal):
    def __init__(self, keys: list, team: dict, view: "TeamSetupView"):
        super().__init__(title="Team Setup")
        self.keys = keys
        self.team = team
        self.view_ref = view
        self.field_inputs = {}

        defaults = {
            "team_name": team.get("team_name") or "",
            "team_code": team.get("team_code") or "",
            "language": team.get("language") or "",
            "timezone": team.get("timezone") or "",
            "rep1": str(team["rep_id"]) if team.get("rep_id") else "",
            "rep2": str(team["rep2_id"]) if team.get("rep2_id") else "",
            "main_clan": team.get("main_clan") or "",
            "secondary_clan": team.get("secondary_clan") or "",
        }
        placeholders = {
            "team_name": "e.g. Galaxy Esports",
            "team_code": "e.g. GXY",
            "language": "e.g. English",
            "timezone": "e.g. UTC+5:30",
            "rep1": "Discord user ID",
            "rep2": "Discord user ID (optional)",
            "main_clan": "e.g. #ABC123",
            "secondary_clan": "e.g. #DEF456 (optional)",
        }

        for key in keys:
            text_input = ui.TextInput(
                label=key,
                default=defaults.get(key, ""),
                placeholder=placeholders.get(key, ""),
                required=False,
                max_length=100
            )
            self.field_inputs[key] = text_input
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        pool = await get_pool()
        gid = str(interaction.guild_id)
        team = self.team
        errors = []
        updates = {}

        for key, text_input in self.field_inputs.items():
            value = text_input.value.strip()
            if not value:
                continue

            if key == "team_code":
                value = value.upper()
                if value != team['team_code']:
                    conflict = await pool.fetchrow(
                        "SELECT 1 FROM teams WHERE guild_id=$1 AND division_code=$2 AND team_code=$3 AND id!=$4",
                        gid, team['division_code'], value, team['id']
                    )
                    if conflict:
                        errors.append(f"Team code **{value}** is already taken.")
                        continue

            elif key in ("main_clan", "secondary_clan"):
                value = normalize_tag(value)
                try:
                    await interaction.client.coc_client.get_clan(value)
                except coc.NotFound:
                    errors.append(f"Clan `{value}` not found.")
                    continue
                except Exception as e:
                    errors.append(f"CoC API error for `{value}`: {e}")
                    continue

            elif key in ("rep1", "rep2"):
                try:
                    int(value)
                except ValueError:
                    errors.append(f"`{key}` must be a Discord user ID (numbers only).")
                    continue

            updates[key] = value

        if errors:
            await interaction.followup.send(embed=discord.Embed(
                description="❌ " + "\n".join(errors),
                color=0xe74c3c
            ))
            return

        col_map = {
            "team_name": "team_name",
            "team_code": "team_code",
            "language": "language",
            "timezone": "timezone",
            "rep1": "rep_id",
            "rep2": "rep2_id",
            "main_clan": "main_clan",
            "secondary_clan": "secondary_clan",
        }

        for key, value in updates.items():
            col = col_map[key]
            await pool.execute(
                f"UPDATE teams SET {col}=$1 WHERE id=$2",
                value, team['id']
            )
            self.view_ref.team[col] = value

        if "team_name" in updates or "team_code" in updates:
            new_name = updates.get("team_name", team['team_name'])
            new_code = updates.get("team_code", team['team_code'])
            await pool.execute(
                """
                UPDATE applications SET team_name=$1, team_code=$2
                WHERE guild_id=$3 AND division_code=$4 AND team_code=$5
                """,
                new_name, new_code, gid, team['division_code'], team['team_code']
            )
            if "team_code" in updates and new_code != team['team_code']:
                app = await pool.fetchrow(
                    "SELECT channel_id FROM applications WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
                    gid, team['division_code'], new_code
                )
                if app:
                    channel = interaction.guild.get_channel(int(app['channel_id']))
                    if channel:
                        try:
                            prefix = channel.name.split("-")[0]
                            await channel.edit(name=f"{prefix}-{new_code.lower()}")
                        except Exception:
                            pass
            self.view_ref.team['team_name'] = new_name
            self.view_ref.team['team_code'] = new_code

        await interaction.followup.send(embed=discord.Embed(
            title="✅ Team Updated",
            description="\n".join(f"**{k}** → `{v}`" for k, v in updates.items()),
            color=0x2ecc71
        ))


class TeamSetupDropdown(ui.Select):
    def __init__(self, view: "TeamSetupView"):
        self.setup_view = view
        options = [
            discord.SelectOption(label=key, value=key)
            for key in SETUP_FIELDS
        ]
        super().__init__(
            placeholder="Select fields to configure...",
            min_values=1,
            max_values=5,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_keys = self.values[:5]
        modal = TeamSettingModal(selected_keys, self.setup_view.team, self.setup_view)
        await interaction.response.send_modal(modal)


class TeamSetupView(ui.View):
    def __init__(self, team: dict):
        super().__init__(timeout=180)
        self.team = dict(team)
        self.message = None
        self._rebuild()

    def _rebuild(self):
        self.clear_items()
        self.add_item(TeamSetupDropdown(self))

        cancel = ui.Button(label="Cancel", style=discord.ButtonStyle.danger, row=1)

        async def cancel_cb(interaction: discord.Interaction):
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)

        cancel.callback = cancel_cb
        self.add_item(cancel)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


async def team_setup(interaction: discord.Interaction, division: str, code: str):
    pool = await get_pool()
    gid = str(interaction.guild_id)

    if not await is_division_admin(interaction):
        await interaction.response.send_message(embed=discord.Embed(
            description="❌ Requires DIVISION_ADMIN.",
            color=0xe74c3c
        ))
        return

    division = division.strip().upper()
    code = code.strip().upper()

    div = await get_division_by_code(gid, division)
    if not div:
        await interaction.response.send_message(embed=discord.Embed(
            description="❌ Division not found.",
            color=0xe74c3c
        ))
        return

    team = await pool.fetchrow(
        "SELECT * FROM teams WHERE guild_id=$1 AND division_code=$2 AND team_code=$3 AND status='active'",
        gid, division, code
    )
    if not team:
        await interaction.response.send_message(embed=discord.Embed(
            description=f"❌ No accepted team with code **{code}** in division **{division}**.",
            color=0xe74c3c
        ))
        return

    view = TeamSetupView(dict(team))
    embed = discord.Embed(
        title=f"Team Setup — {team['team_name']}",
        description="```\nteam_name\nteam_code\nlanguage\ntimezone\nrep1\nrep2\nmain_clan\nsecondary_clan\n```",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Select up to 5 fields at a time to configure.")
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()
