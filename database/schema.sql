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
