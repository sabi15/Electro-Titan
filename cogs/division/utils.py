import re
from database.db import get_pool

async def check_division_admin(interaction):
    from config import BOT_DEV_ID
    if interaction.user.id == BOT_DEV_ID:
        return True
    pool = await get_pool()
    role_ids = [str(role.id) for role in interaction.user.roles]
    if not role_ids:
        return False
    row = await pool.fetchrow(
        """
        SELECT 1 FROM perm_assignments
        WHERE guild_id = $1
        AND role_id = ANY($2::text[])
        AND permission = 'DIVISION_ADMIN'
        """,
        str(interaction.guild_id), role_ids
    )
    return row is not None


async def get_division_by_code(pool, guild_id: str, code: str):
    return await pool.fetchrow(
        "SELECT * FROM divisions WHERE guild_id = $1 AND code = $2",
        guild_id, code.upper()
    )


async def get_division_settings(pool, division_id: int):
    rows = await pool.fetch(
        "SELECT key, value FROM division_settings WHERE division_id = $1",
        division_id
    )
    return {row["key"]: row["value"] for row in rows}


async def upsert_setting(pool, division_id: int, key: str, value: str):
    await pool.execute(
        """
        INSERT INTO division_settings (division_id, key, value)
        VALUES ($1, $2, $3)
        ON CONFLICT (division_id, key) DO UPDATE SET value = EXCLUDED.value
        """,
        division_id, key, value
    )


SETTINGS_PAGES = [
    [
        "max_rostersize",
        "min_roster_bd",
        "allowed_th_levels",
        "max_clan_level",
        "max_accounts_per_user",
        "max_attacks",
        "max_adds",
        "roster_lock",
        "require_account_link",
        "allow_dual_players",
        "allow_player_transfer",
        "allow_subs",
        "allow_secondary_clan",
        "rep_role_id",
        "auto_rep_roles",
    ],
    [
        "accept_applications",
        "app_message",
        "app_requirements",
        "app_role_id",
        "acceptance_message",
        "require_transaction_approval",
        "transaction_log_channel_id",
        "enforce_transaction_restrictions",
        "forfeit_score",
        "discord_invite",
    ],
    [
        "war_mode",
        "standing_criteria",
        "one_hit",
        "max_def",
        "no_hitup",
        "nego_message",
        "schedule_reminder",
        "multiple_stream",
        "claim_time",
        "claim_dm",
        "claim_notification",
        "mediation_category_id",
        "tournament_description",
        "tournament_rules",
    ],
]

SETTING_DEFAULTS = {
    "roster_lock": "false",
    "require_account_link": "false",
    "allow_dual_players": "true",
    "allow_player_transfer": "false",
    "allow_subs": "true",
    "allow_secondary_clan": "true",
    "auto_rep_roles": "false",
    "accept_applications": "false",
    "require_transaction_approval": "false",
    "enforce_transaction_restrictions": "false",
    "one_hit": "false",
    "no_hitup": "true",
    "multiple_stream": "true",
    "schedule_reminder": "1",
    "max_def": "1",
    "standing_criteria": "w:d/t:d/l:a/asd:d/apd:d",
    "war_mode": "normal",
    "app_requirements": "rep1,clan1,roster",
    "app_message": (
        "> `/team addplayer` — Add a player to your roster\n"
        "> `/team delplayer` — Remove a player from your roster\n"
        "> `/team setclan` — Set your main or secondary clan\n"
        "> `/team settimezone` — Set your team timezone\n"
        "> `/team setlanguage` — Set your team language\n"
        "> `/team setrep` — Change your team representative\n"
        "> `/team addlogo` — Upload your team logo\n"
        "> `/team show` — Preview your application\n"
        "> `/team complete` — Submit your application\n"
        "> `/team withdraw` — Withdraw your application"
    ),
    "acceptance_message": (
        "Congratulations! Your team was accepted into **{division_name}** "
        "with the team code ***{team_code}***. Please remember this code, "
        "you will need it for all future bot commands regarding your team."
    ),
    "nego_message": (
        "Hello {reps}! This is the negotiation channel for "
        "**{teamA}** vs **{teamB}**.\n"
        "Schedule: {sch_start} — {sch_end}\n"
        "Please coordinate your match time here."
    ),
    "claim_notification": (
        "{reps} Your match will be streamed. Please make sure to grant the "
        "streamer(s) access to your clan if requested and to abide by "
        "stream-related attacking order/windows if applicable. "
        "You can check **`/streams upcoming`** for more details."
    ),
}

BOOL_SETTINGS = {
    "roster_lock", "require_account_link", "allow_dual_players",
    "allow_player_transfer", "allow_subs", "allow_secondary_clan",
    "auto_rep_roles", "accept_applications", "require_transaction_approval",
    "enforce_transaction_restrictions", "one_hit", "no_hitup", "multiple_stream",
}

WAR_MODES = {"normal", "legend_1", "legend_2", "legend_3", "esports"}

DISCORD_INVITE_RE = re.compile(
    r"^(https?://)?(discord\.gg|discord\.com/invite)/[a-zA-Z0-9-]+$"
)

FORFEIT_SCORE_RE = re.compile(
    r"^\d+,\d+(\.\d+)?-\d+,\d+(\.\d+)?$"
)

MIN_ROSTER_BD_RE = re.compile(
    r"^\d+-\d+(/\d+-\d+)*$"
)

STANDING_CRITERIA_VALID = {
    "w", "t", "l", "p",
    "sg", "asg", "sl", "asl", "sd", "asd",
    "pg", "apg", "pl", "apl", "pd", "apd", "aad"
}


def validate_setting(key: str, value: str) -> str | None:
    """
    Returns an error string if invalid, or None if valid.
    """
    value = value.strip()

    if key in BOOL_SETTINGS:
        if value.lower() not in ("true", "false"):
            return f"❌ **{key}** must be `true` or `false`."

    elif key in ("max_rostersize", "max_clan_level", "max_accounts_per_user",
                 "max_attacks", "max_adds", "schedule_reminder", "max_def", "claim_time"):
        if not value.isdigit():
            return f"❌ **{key}** must be a whole number."

    elif key == "min_roster_bd":
        if not MIN_ROSTER_BD_RE.match(value):
            return (
                f"❌ **min_roster_bd** format is invalid.\n"
                f"Examples: `18-5` or `18-2/17-1/16-1/15-1`"
            )

    elif key == "allowed_th_levels":
        parts = value.split("/")
        if not all(p.strip().isdigit() for p in parts):
            return f"❌ **allowed_th_levels** must be like `18` or `18/17/16`."

    elif key == "war_mode":
        if value.lower() not in WAR_MODES:
            return (
                f"❌ **war_mode** must be one of: "
                f"`normal`, `legend_1`, `legend_2`, `legend_3`, `esports`."
            )

    elif key == "discord_invite":
        if not DISCORD_INVITE_RE.match(value):
            return f"❌ **discord_invite** is not a valid Discord invite link."

    elif key == "forfeit_score":
        if not FORFEIT_SCORE_RE.match(value):
            return (
                f"❌ **forfeit_score** format is invalid.\n"
                f"Example: `12,85.7-10,73.5`"
            )

    elif key == "standing_criteria":
        parts = value.split("/")
        for part in parts:
            segments = part.split(":")
            if len(segments) != 2:
                return f"❌ **standing_criteria** format invalid. Example: `w:d/t:d/l:a/asd:d/apd:d`"
            stat, order = segments
            if stat not in STANDING_CRITERIA_VALID or order not in ("a", "d"):
                return (
                    f"❌ **standing_criteria** has invalid entry `{part}`.\n"
                    f"Order must be `a` (ascending) or `d` (descending)."
                )

    elif key == "app_requirements":
        valid = {"rep1", "rep2", "clan1", "clan2", "language", "timezone", "logo", "roster"}
        parts = [p.strip() for p in value.split(",")]
        invalid = [p for p in parts if p not in valid]
        if invalid:
            return (
                f"❌ **app_requirements** has invalid value(s): `{', '.join(invalid)}`.\n"
                f"Valid: `rep1, rep2, clan1, clan2, language, timezone, logo, roster`"
            )

    elif key == "rep_role_id":
        if not value.isdigit():
            return f"❌ **rep_role_id** must be a valid Discord role ID (numbers only)."

    elif key == "transaction_log_channel_id":
        if not value.isdigit():
            return f"❌ **transaction_log_channel_id** must be a valid Discord channel ID (numbers only)."

    elif key == "mediation_category_id":
        if not value.isdigit():
            return f"❌ **mediation_category_id** must be a valid Discord category ID (numbers only)."

    return None
