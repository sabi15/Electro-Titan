import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.create import create
from .commands.delete import delete
from .commands.deactivate import deactivate
from .commands.info import info
from .commands.setlogo import setlogo
from .commands.newseason import newseason
from .commands.setup import setup as setup_cmd
from .commands.addgroup import addgroup
from .commands.delgroup import delgroup
from .commands.draw import draw
from .commands.groups import groups
from .commands.participants import participants


class Division(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.division = app_commands.Group(
            name="division",
            description="Division management commands"
        )

        self.division.command(name="create", description="Create a division")(create)
        self.division.command(name="delete", description="Delete a division")(delete)
        self.division.command(name="deactivate", description="Deactivate a division")(deactivate)
        self.division.command(name="info", description="View division info")(info)
        self.division.command(name="setlogo", description="Set division logo")(setlogo)
        self.division.command(name="newseason", description="Start a new season")(newseason)
        self.division.command(name="setup", description="Setup division")(setup_cmd)
        self.division.command(name="addgroup", description="Add a group")(addgroup)
        self.division.command(name="delgroup", description="Delete a group")(delgroup)
        self.division.command(name="draw", description="Draw groups")(draw)
        self.division.command(name="groups", description="View groups")(groups)
        self.division.command(name="participants", description="View participants")(participants)

        bot.tree.add_command(self.division)

    async def cog_unload(self):
        self.bot.tree.remove_command("division")


async def setup(bot):
    await bot.add_cog(Division(bot))
