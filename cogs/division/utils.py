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
        "max_rostersize", "mediation_category_id", "min_roster_bd",
        "nego_message", "no_dip", "no_hitup", "one_hit",
        "rep_role_id", "require_account_claims", "require_transaction_approval",
        "roster_lock", "schedule_reminder", "standing_criteria",
        "stream_call_stacking", "stream_claim_cutoff_minutes",
    ],
    [
        "stream_claim_dm_message", "stream_notification_message",
        "tournament_description", "tournament_rules",
        "transaction_log_channel_id", "war_mode", "acceptance_message",
        "accept_applications", "allowed_th_levels", "allow_dual_players",
        "allow_player_transfer", "allow_secondary_clan", "allow_subs",
        "app_message", "app_requirements",
    ],
    [
        "app_role_id", "auto_rep_roles", "discord_invite",
        "forfeit_score", "enforce_transaction_restrictions",
        "gfx_timezone", "match_tiebreakers", "max_accounts_per_user",
        "max_adds", "max_attacks", "max_clan_level",
    ]
]
