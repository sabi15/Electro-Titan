import discord
from discord import app_commands
from discord.ext import commands
import coc
import asyncio
import traceback
from config import BOT_TOKEN, COC_EMAIL, COC_PASSWORD, TEST_GUILD_ID
from database.db import init_pool, get_pool

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "cogs.dev",
    "cogs.acc",
    "cogs.panel",
    "cogs.league",
    "cogs.division",
    "cogs.team",
    "cogs.schedule",
    "cogs.match",
    "cogs.transaction",
    "cogs.blist",
    "cogs.fp",
    "cogs.feed",
    "cogs.export",
    "cogs.banner",
]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"✅ Connected to {len(bot.guilds)} guild(s)")
    try:
        guild = discord.Object(id=TEST_GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} command(s) to test guild.")
    except Exception:
        print(f"❌ Failed to sync commands:\n{traceback.format_exc()}")

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Error in event '{event}':")
    traceback.print_exc()

@bot.event
async def on_guild_join(guild):
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT whitelisted FROM whitelisted_servers WHERE server_id=$1",
        str(guild.id)
    )
    if row and not row["whitelisted"]:
        try:
            await guild.leave()
        except Exception:
            pass

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"❌ Slash command error in /{interaction.command.name}:")
    traceback.print_exc()
    try:
        await interaction.followup.send(f"❌ An error occurred: `{error}`")
    except Exception:
        pass

async def main():
    print("⏳ Connecting to database...")
    try:
        await init_pool()
        print("✅ Database connected.")
    except Exception:
        print(f"❌ Database connection failed:\n{traceback.format_exc()}")
        return

    print("⏳ Logging into CoC API...")
    try:
        coc_client = coc.Client()
        await coc_client.login(COC_EMAIL, COC_PASSWORD)
        bot.coc_client = coc_client
        print("✅ CoC API connected.")
    except Exception:
        print(f"❌ CoC API login failed:\n{traceback.format_exc()}")
        return

    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded cog: {cog}")
        except Exception:
            print(f"❌ Failed to load cog '{cog}':\n{traceback.format_exc()}")

    try:
        guild = discord.Object(id=TEST_GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} command(s) to test guild.")
    except Exception:
        print(f"❌ Failed to sync commands:\n{traceback.format_exc()}")

    print("⏳ Starting bot...")
    try:
        await bot.start(BOT_TOKEN)
    except Exception:
        print(f"❌ Bot failed to start:\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
