import discord
from database.db import get_pool
from cogs.team.utils import is_division_admin, get_division_by_code


class TeamSetupModal(discord.ui.Modal):
    def __init__(self, team, div):
        super().__init__(title=f"Setup: {team['team_name']}")
        self.team = team
        self.div = div

        self.team_name_input = discord.ui.TextInput(
            label="Team Name",
            default=team['team_name'] or "",
            required=True,
            max_length=50
        )
        self.team_code_input = discord.ui.TextInput(
            label="Team Code",
            default=team['team_code'] or "",
            required=True,
            max_length=20
        )
        self.language_input = discord.ui.TextInput(
            label="Language",
            default=team['language'] or "",
            required=False,
            max_length=50
        )
        self.timezone_input = discord.ui.TextInput(
            label="Timezone (e.g. UTC+5:30)",
            default=team['timezone'] or "",
            required=False,
            max_length=30
        )
        self.clans_input = discord.ui.TextInput(
            label="Main Clan Tag | Secondary Clan Tag (optional)",
            placeholder="#ABC123 | #DEF456",
            default=f"{team['main_clan'] or ''} | {team['secondary_clan'] or ''}".strip(" |"),
            required=False,
            max_length=40
        )

        self.add_item(self.team_name_input)
        self.add_item(self.team_code_input)
        self.add_item(self.language_input)
        self.add_item(self.timezone_input)
        self.add_item(self.clans_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        pool = await get_pool()
        gid = str(interaction.guild_id)
        team = self.team

        from utils.helpers import normalize_tag
        import coc

        new_name = self.team_name_input.value.strip()
        new_code = self.team_code_input.value.strip().upper()
        new_language = self.language_input.value.strip() or None
        new_timezone = self.timezone_input.value.strip() or None
        clans_raw = self.clans_input.value.strip()

        clan_parts = [c.strip() for c in clans_raw.split("|")]
        new_main = normalize_tag(clan_parts[0]) if len(clan_parts) > 0 and clan_parts[0] else None
        new_secondary = normalize_tag(clan_parts[1]) if len(clan_parts) > 1 and clan_parts[1] else None

        errors = []

        if new_main:
            try:
                await interaction.client.coc_client.get_clan(new_main)
            except coc.NotFound:
                errors.append(f"Main clan `{new_main}` not found.")
            except Exception as e:
                errors.append(f"CoC API error for main clan: {e}")

        if new_secondary:
            try:
                await interaction.client.coc_client.get_clan(new_secondary)
            except coc.NotFound:
                errors.append(f"Secondary clan `{new_secondary}` not found.")
            except Exception as e:
                errors.append(f"CoC API error for secondary clan: {e}")

        if errors:
            await interaction.followup.send(embed=discord.Embed(
                description="❌ " + "\n".join(errors),
                color=0xe74c3c
            ))
            return

        if new_code != team['team_code']:
            conflict = await pool.fetchrow(
                "SELECT 1 FROM teams WHERE guild_id=$1 AND division_code=$2 AND team_code=$3 AND id!=$4",
                gid, team['division_code'], new_code, team['id']
            )
            if conflict:
                await interaction.followup.send(embed=discord.Embed(
                    description=f"❌ Team code **{new_code}** is already taken.",
                    color=0xe74c3c
                ))
                return

        await pool.execute(
            """
            UPDATE teams
            SET team_name=$1, team_code=$2, language=$3, timezone=$4, main_clan=$5, secondary_clan=$6
            WHERE id=$7
            """,
            new_name, new_code, new_language, new_timezone, new_main, new_secondary, team['id']
        )

        await pool.execute(
            """
            UPDATE applications SET team_name=$1, team_code=$2
            WHERE guild_id=$3 AND division_code=$4 AND team_code=$5
            """,
            new_name, new_code, gid, team['division_code'], team['team_code']
        )

        if new_code != team['team_code']:
            app = await pool.fetchrow(
                "SELECT * FROM applications WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
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

        await interaction.followup.send(embed=discord.Embed(
            description=f"✅ Team **{new_name}** (`{new_code}`) updated successfully.",
            color=0x2ecc71
        ))


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

    modal = TeamSetupModal(team, div)
    await interaction.response.send_modal(modal)
