import discord
from discord import app_commands
from discord.ext import commands as ext_commands
from .commands.add import add
from .commands.remove import remove
from .commands.view import view
from .commands.history import history

class acc(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.acc = app_commands.Group(
            name="acc",
            description="public commands"
        )
        self.acc.command(name="add", description="Add a permission to a role")(add)
        self.acc.command(name="view", description="Remove a permission from a role")(view)
        self.acc.command(name="history", description="Clear all perms in this server")(history)
        self.acc.command(name="remove", description="List all perm assignments in this server")(remove)
        bot.tree.add_command(self.acc)

    async def cog_unload(self):
        self.bot.tree.remove_command("acc")


async def setup(bot):
    await bot.add_cog(acc(bot))
