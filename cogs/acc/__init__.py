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
           description="Account management commands"
       )

       self.acc.command(name="add", description="Link your CoC account with Discord")(
           app_commands.describe(
               tag="Your Clash of Clans player tag (e.g. #ABC123)",
               api="Your API token from in-game settings"
           )(add)
       )
       self.acc.command(name="view", description="View linked CoC accounts")(
           app_commands.describe(
               tag="A CoC player tag to look up",
               user="A Discord user to look up"
           )(view)
       )
       self.acc.command(name="history", description="Check account link history")(
           app_commands.describe(
               tag="A CoC player tag to check history for",
               user="A Discord user to check history for"
           )(history)
       )
       self.acc.command(name="remove", description="Unlink a CoC account from your Discord")(
           app_commands.describe(
               tag="The CoC player tag to remove (e.g. #ABC123)"
           )(remove)
       )

       bot.tree.add_command(self.acc)

   async def cog_unload(self):
       self.bot.tree.remove_command("acc")


async def setup(bot):
   await bot.add_cog(acc(bot))
