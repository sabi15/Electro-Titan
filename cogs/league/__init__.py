from discord.ext import commands as ext_commands
from discord import app_commands
from cogs.league.commands.create import league_create
from cogs.league.commands.delete import league_delete
from cogs.league.commands.setup import league_setup
from cogs.league.commands.addlogo import league_addlogo
from cogs.league.commands.list import league_list
from cogs.league.commands.info import league_info


class League(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="league", description="League management commands")

        self.group.command(name="create", description="Create a new league")(
            app_commands.describe(name="League name", code="Unique league code (e.g. GBS-OL)")(league_create)
        )
        self.group.command(name="delete", description="Delete a league")(
            app_commands.describe(code="League code")(league_delete)
        )
        self.group.command(name="setup", description="Configure league settings")(
            app_commands.describe(code="League code")(league_setup)
        )
        self.group.command(name="addlogo", description="Add or update league logo")(
            app_commands.describe(code="League code", attachment="Image file")(league_addlogo)
        )
        self.group.command(name="list", description="List all leagues in this server")(league_list)
        self.group.command(name="info", description="View league details")(
            app_commands.describe(code="League code")(league_info)
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("league")


async def setup(bot):
    await bot.add_cog(league(bot))
