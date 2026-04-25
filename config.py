import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_DEV_ID = int(os.getenv("BOT_DEV"))
TEST_GUILD_ID = 1488389148443283637
COC_EMAIL = os.getenv("COC_EMAIL")
COC_PASSWORD = os.getenv("COC_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

VALID_PERMS = [
    "MANAGE_MEDIA",
    "MANAGE_NEGOTIATIONS",
    "MANAGE_TRANSACTIONS",
    "REPRESENTATIVE",
    "STREAMER",
    "LEAGUE_ADMIN",
    "DIVISION_ADMIN",
    "MANAGE_BANLIST",
    "MANAGE_ROSTER",
    "MANAGE_MATCHES",
    "MANAGE_TEAMS",
    "MANAGE_APPLICATIONS",
]

WHITELIST_MESSAGE = (
    "⚠️ This server is not whitelisted for RIKA.\n"
    "Contact **might.over.meta** on Discord to get whitelisted."
)

ACC_INVITE_MESSAGE = (
    "💡 Want full access to RIKA's features? "
    "Join our community: https://discord.gg/75UADeZg4K"
)
