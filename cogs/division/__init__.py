import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.create import division_create
from .commands.deactivate import division_deactivate
from .commands.delete import division_delete
from .commands.setup import division_setup
from .commands.addgroup import division_addgroup
from .commands.delgroup import division_delgroup
from .commands.draw import division_draw
from .commands.groups import division_groups
from .commands.info import division_info
from .commands.setlogo import division_setlogo
from .commands.newseason import division_newseason
from .commands.participants import division_participants


class Division(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.division = app_commands.Group(
            name="division",
            description="Division management commands"
        )
        self.division.command(name="create", description="Create a new division")(division_create)
        self.division.command(name="deactivate", description="Toggle a division active/inactive")(division_deactivate)
        self.division.command(name="delete", description="Permanently delete a division")(division_delete)
        self.division.command(name="setup", description="Configure division settings")(division_setup)
        self.division.command(name="addgroup", description="Add a group to a schedule")(division_addgroup)
        self.division.command(name="delgroup", description="Delete a group from a schedule")(division_delgroup)
        self.division.command(name="draw", description="Randomly assign participants into groups")(division_draw)
        self.division.command(name="groups", description="View all groups in a division")(division_groups)
        self.division.command(name="info", description="View details of a division")(division_info)
        self.division.command(name="setlogo", description="Set the logo for a division")(division_setlogo)
        self.division.command(name="newseason", description="Archive current season and start fresh")(division_newseason)
        self.division.command(name="participants", description="View all participants in a division")(division_participants)
        bot.tree.add_command(self.division)

    async def cog_unload(self):
        self.bot.tree.remove_command("division")


async def setup(bot):
    await bot.add_cog(Division(bot))
