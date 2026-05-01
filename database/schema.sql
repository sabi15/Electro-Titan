-- Whitelisted Servers
CREATE TABLE IF NOT EXISTS whitelisted_servers (
    server_id TEXT PRIMARY KEY,
    whitelisted BOOLEAN DEFAULT FALSE
);

-- Permissions
CREATE TABLE IF NOT EXISTS perm_assignments (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    permission TEXT NOT NULL,
    UNIQUE(guild_id, role_id, permission)
);

-- Disabled Cogs
CREATE TABLE IF NOT EXISTS disabled_cogs (
    id SERIAL PRIMARY KEY,
    server_id TEXT NOT NULL,
    cog_name TEXT NOT NULL,
    UNIQUE(server_id, cog_name)
);

-- Acc Accounts
CREATE TABLE IF NOT EXISTS acc_accounts (
    id          SERIAL PRIMARY KEY,
    discord_id  BIGINT NOT NULL,
    tag         TEXT NOT NULL UNIQUE,
    ign         TEXT NOT NULL,
    th_level    INTEGER NOT NULL,
    claimed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_acc_accounts_discord ON acc_accounts(discord_id);
CREATE INDEX IF NOT EXISTS idx_acc_accounts_tag ON acc_accounts(tag);

-- Acc History
CREATE TABLE IF NOT EXISTS acc_history (
    id            SERIAL PRIMARY KEY,
    discord_id    BIGINT NOT NULL,
    tag           TEXT NOT NULL,
    ign           TEXT NOT NULL,
    th_level      INTEGER NOT NULL,
    action        TEXT NOT NULL CHECK (action IN ('claimed', 'removed')),
    actioned_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_acc_history_discord ON acc_history(discord_id);
CREATE INDEX IF NOT EXISTS idx_acc_history_tag ON acc_history(tag);

-- Acc Usage
CREATE TABLE IF NOT EXISTS acc_usage (
    discord_id   BIGINT PRIMARY KEY,
    use_count    INTEGER NOT NULL DEFAULT 0
);

-- Leagues
CREATE TABLE IF NOT EXISTS leagues (
    id           SERIAL PRIMARY KEY,
    guild_id     BIGINT NOT NULL,
    name         TEXT NOT NULL,
    code         TEXT NOT NULL,
    description  TEXT,
    logo_url     TEXT,
    invite_link  TEXT,
    ban_duration INTEGER,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (guild_id, code)
);

CREATE TABLE IF NOT EXISTS divisions (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    league_code TEXT NOT NULL,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    season TEXT NOT NULL DEFAULT '1',
    logo_url TEXT,
    transaction_log_channel_id TEXT,
    rep_role_id TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    UNIQUE(guild_id, code)
);

CREATE TABLE IF NOT EXISTS division_settings (
    id SERIAL PRIMARY KEY,
    division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT,
    UNIQUE(division_id, key)
);

CREATE TABLE IF NOT EXISTS division_schedules (
    id SERIAL PRIMARY KEY,
    division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    UNIQUE(division_id, name)
);

CREATE TABLE IF NOT EXISTS division_groups (
    id SERIAL PRIMARY KEY,
    division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
    schedule_name TEXT NOT NULL,
    group_name TEXT NOT NULL,
    team_codes TEXT[] NOT NULL DEFAULT '{}',
    UNIQUE(division_id, schedule_name, group_name)
);

CREATE TABLE IF NOT EXISTS division_participants (
    id SERIAL PRIMARY KEY,
    division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
    team_code TEXT NOT NULL,
    season TEXT NOT NULL,
    timezone TEXT,
    UNIQUE(division_id, team_code, season)
);

CREATE TABLE IF NOT EXISTS division_season_archive (
    id SERIAL PRIMARY KEY,
    division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
    season TEXT NOT NULL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    settings_snapshot JSONB,
    groups_snapshot JSONB
);

CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    team_code TEXT NOT NULL,
    team_name TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    rep_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(guild_id, division_code, team_code)
);

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    team_code TEXT NOT NULL,
    team_name TEXT NOT NULL,
    rep_id TEXT,
    rep2_id TEXT,
    main_clan TEXT,
    secondary_clan TEXT,
    timezone TEXT,
    language TEXT,
    logo_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(guild_id, division_code, team_code)
);

CREATE TABLE IF NOT EXISTS rosters (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    team_code TEXT NOT NULL,
    player_tag TEXT NOT NULL,
    claimed_by TEXT,
    UNIQUE(guild_id, division_code, player_tag)
);
