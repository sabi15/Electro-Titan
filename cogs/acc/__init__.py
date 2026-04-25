from discord import app_commands
from discord.ext import commands
from .add import add
from .remove import remove
from .history import history
from .warweight import warweight

acc_group = app_commands.Group(name="acc", description="Account commands")
acc_group.command(name="add")(add)
acc_group.command(name="remove")(remove)
acc_group.command(name="history")(history)
acc_group.command(name="warweight")(warweight)

async def setup(bot):
    bot.tree.add_command(acc_group)
