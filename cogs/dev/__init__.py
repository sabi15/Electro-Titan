import discord
from discord import app_commands
from discord.ext import commands as ext_commands
from .commands.addperms import addperms
from .commands.delperms import delperms
from .commands.clearallperms import clearallperms
from .commands.permlist import permlist
from .commands.blacklist import blacklist
from .commands.whitelist import whitelist
from .commands.disablecog import disablecog
from .commands.enablecog import enablecog
from .commands.setup import setup as setup_cmd
from .commands.status import status
from .commands.migrate import dev_migrate



class Dev(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dev = app_commands.Group(
            name="dev",
            description="Bot developer commands"
        )
        self.dev.command(name="addperms", description="Add a permission to a role")(addperms)
        self.dev.command(name="delperms", description="Remove a permission from a role")(delperms)
        self.dev.command(name="clearallperms", description="Clear all perms in this server")(clearallperms)
        self.dev.command(name="permlist", description="List all perm assignments in this server")(permlist)
        self.dev.command(name="blacklist", description="Blacklist a server")(blacklist)
        self.dev.command(name="whitelist", description="Whitelist a server")(whitelist)
        self.dev.command(name="disablecog", description="Disable a cog for a server")(disablecog)
        self.dev.command(name="enablecog", description="Enable a cog for a server")(enablecog)
        self.dev.command(name="setup", description="View server setup info")(setup_cmd)
        self.dev.command(name="status", description="View bot status")(status)
        self.dev.command(name="migrate", description="Run DB migration")(dev_migrate)
        bot.tree.add_command(self.dev)

    async def cog_unload(self):
        self.bot.tree.remove_command("dev")


async def setup(bot):
    await bot.add_cog(Dev(bot))
