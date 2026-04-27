-- Permissions
CREATE TABLE IF NOT EXISTS perm_assignments (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    permission TEXT NOT NULL,
    UNIQUE(guild_id, role_id, permission)
);

-- Claims
CREATE TABLE IF NOT EXISTS claims (
    id SERIAL PRIMARY KEY,
    discord_id TEXT NOT NULL,
    player_tag TEXT NOT NULL UNIQUE,
    api_token TEXT NOT NULL,
    claimed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leagues
CREATE TABLE leagues (
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


-- Divisions
CREATE TABLE IF NOT EXISTS divisions (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    code TEXT NOT NULL,
    league_code TEXT,
    active BOOLEAN DEFAULT TRUE,
    logo_url TEXT,
    UNIQUE(guild_id, code)
);

-- Tournament Settings
CREATE TABLE IF NOT EXISTS tournament_settings (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    UNIQUE(guild_id, division_code, setting_key)
);

-- Applications
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    team_code TEXT NOT NULL,
    team_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    channel_id TEXT,
    rep_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(guild_id, division_code, team_code)
);

-- Application Data
CREATE TABLE IF NOT EXISTS application_data (
    id SERIAL PRIMARY KEY,
    application_id INT REFERENCES applications(id) ON DELETE CASCADE,
    field_key TEXT NOT NULL,
    field_value TEXT
);

-- Teams
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    team_code TEXT NOT NULL,
    team_name TEXT NOT NULL,
    rep_id TEXT,
    language TEXT,
    timezone TEXT,
    main_clan TEXT,
    secondary_clan TEXT,
    logo_url TEXT,
    UNIQUE(guild_id, division_code, team_code)
);

-- Rosters
CREATE TABLE IF NOT EXISTS rosters (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    team_code TEXT NOT NULL,
    player_tag TEXT NOT NULL,
    UNIQUE(guild_id, division_code, team_code, player_tag)
);

-- Team Quotas
CREATE TABLE IF NOT EXISTS team_quotas (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    team_code TEXT NOT NULL,
    quota_key TEXT NOT NULL,
    quota_value INT DEFAULT 0,
    UNIQUE(guild_id, division_code, team_code, quota_key)
);

-- Schedules
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    schedule_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    play_type TEXT,
    UNIQUE(guild_id, division_code, schedule_name)
);

-- Groups
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    schedule_name TEXT NOT NULL,
    group_name TEXT NOT NULL,
    UNIQUE(guild_id, division_code, schedule_name, group_name)
);

-- Group Members
CREATE TABLE IF NOT EXISTS group_members (
    id SERIAL PRIMARY KEY,
    group_id INT REFERENCES groups(id) ON DELETE CASCADE,
    team_code TEXT NOT NULL
);

-- Matches
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    schedule_name TEXT NOT NULL,
    team_a TEXT NOT NULL,
    team_b TEXT NOT NULL,
    channel_id TEXT,
    status TEXT DEFAULT 'pending'
);

-- Match Times
CREATE TABLE IF NOT EXISTS match_times (
    id SERIAL PRIMARY KEY,
    match_id INT REFERENCES matches(id) ON DELETE CASCADE,
    proposed_time TIMESTAMPTZ,
    proposed_by TEXT,
    confirmed BOOLEAN DEFAULT FALSE
);

-- Match Results
CREATE TABLE IF NOT EXISTS match_results (
    id SERIAL PRIMARY KEY,
    match_id INT REFERENCES matches(id) ON DELETE CASCADE,
    winner TEXT,
    score_a INT,
    score_b INT,
    recorded_by TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    team_code TEXT NOT NULL,
    player_tag TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    requested_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Banlist
CREATE TABLE IF NOT EXISTS banlist (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    player_tag TEXT NOT NULL,
    reason TEXT,
    ban_level INT DEFAULT 1,
    expiry_date DATE,
    banned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(guild_id, player_tag)
);

-- Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    player_tag TEXT NOT NULL,
    incident_type TEXT,
    detail TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feeds
CREATE TABLE IF NOT EXISTS feeds (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    feed_type TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    UNIQUE(guild_id, division_code, feed_type)
);

-- Languages
CREATE TABLE IF NOT EXISTS languages (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    language TEXT NOT NULL,
    UNIQUE(guild_id, division_code, language)
);

-- GFX Templates
CREATE TABLE IF NOT EXISTS gfx_templates (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    template_type TEXT NOT NULL,
    template_url TEXT,
    mask_url TEXT,
    font TEXT,
    UNIQUE(guild_id, division_code, template_type)
);

-- Poster Layouts
CREATE TABLE IF NOT EXISTS poster_layouts (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    division_code TEXT NOT NULL,
    template_type TEXT NOT NULL,
    template_url TEXT,
    mask_url TEXT,
    font TEXT DEFAULT 'default',
    UNIQUE(guild_id, division_code, template_type)
);

-- Poster Regions
CREATE TABLE IF NOT EXISTS poster_regions (
    id SERIAL PRIMARY KEY,
    layout_id INT REFERENCES poster_layouts(id) ON DELETE CASCADE,
    region_index INT NOT NULL,
    x INT NOT NULL,
    y INT NOT NULL,
    width INT NOT NULL,
    height INT NOT NULL,
    component TEXT,
    h_align TEXT DEFAULT 'center',
    v_align TEXT DEFAULT 'center',
    color_overlay TEXT,
    region_name TEXT,
    UNIQUE(layout_id, region_index)
);

-- Panels
CREATE TABLE IF NOT EXISTS panels (
    id SERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    message_id TEXT NOT NULL
);

-- Whitelisted Servers
CREATE TABLE IF NOT EXISTS whitelisted_servers (
    server_id TEXT PRIMARY KEY,
    whitelisted BOOLEAN DEFAULT FALSE
);

-- Disabled Cogs
CREATE TABLE IF NOT EXISTS disabled_cogs (
    id SERIAL PRIMARY KEY,
    server_id TEXT NOT NULL,
    cog_name TEXT NOT NULL,
    UNIQUE(server_id, cog_name)
);

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

CREATE TABLE IF NOT EXISTS acc_usage (
    discord_id   BIGINT PRIMARY KEY,
    use_count    INTEGER NOT NULL DEFAULT 0
);
