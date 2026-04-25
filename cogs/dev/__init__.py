from discord.ext import commands
from .commands.addperms import addperms
from .commands.delperms import delperms
from .commands.clearallperms import clearallperms
from .commands.permlist import permlist
from .commands.blacklist import blacklist
from .commands.whitelist import whitelist
from .commands.disablecog import disablecog
from .commands.enablecog import enablecog
from .commands.setup import setup
from .commands.status import status
from discord import app_commands


class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    dev = app_commands.Group(name="dev", description="Bot developer commands")

    dev.command(name="addperms", description="Add a permission to a role")(addperms)
    dev.command(name="delperms", description="Remove a permission from a role")(delperms)
    dev.command(name="clearallperms", description="Clear all perms in this server")(clearallperms)
    dev.command(name="permlist", description="List all perm assignments in this server")(permlist)
    dev.command(name="blacklist", description="Blacklist a server")(blacklist)
    dev.command(name="whitelist", description="Whitelist a server")(whitelist)
    dev.command(name="disablecog", description="Disable a cog for a server")(disablecog)
    dev.command(name="enablecog", description="Enable a cog for a server")(enablecog)
    dev.command(name="setup", description="View server setup info")(setup)
    dev.command(name="status", description="View bot status")(status)


async def setup(bot):
    await bot.add_cog(Dev(bot))
