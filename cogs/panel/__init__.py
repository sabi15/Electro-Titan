from discord.ext import commands as ext_commands
from discord import app_commands
from cogs.panel.commands.send import send, ClaimView


class Panel(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="panel", description="Panel management commands")

        self.group.command(name="send", description="Send the account claim panel")(send)

        bot.tree.add_command(self.group)
        bot.add_view(ClaimView())  # Re-registers persistent view on restart

    async def cog_unload(self):
        self.bot.tree.remove_command("panel")


async def setup(bot):
    await bot.add_cog(Panel(bot))
