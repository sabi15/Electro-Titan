from discord.ext import commands as ext_commands
from discord import app_commands
from cogs.team.commands.register import team_register
from cogs.team.commands.setclan import team_setclan
from cogs.team.commands.setlanguage import team_setlanguage
from cogs.team.commands.settimezone import team_settimezone
from cogs.team.commands.setrep import team_setrep
from cogs.team.commands.addlogo import team_addlogo
from cogs.team.commands.addplayer import team_addplayer
from cogs.team.commands.delplayer import team_delplayer
from cogs.team.commands.show import team_show
from cogs.team.commands.complete import team_complete
from cogs.team.commands.withdraw import team_withdraw
from cogs.team.commands.accept import team_accept
from cogs.team.commands.reject import team_reject
from cogs.team.commands.setup import team_setup
from cogs.team.commands.info import team_info
from cogs.team.commands.deletechannels import team_deletechannels


class Team(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="team", description="Team management commands")

        self.group.command(name="register", description="Register your team for a division")(
            app_commands.describe(
                division="Division code",
                team_name="Your team name",
                team_code="Unique team code (e.g. TSM)"
            )(team_register)
        )
        self.group.command(name="setclan", description="Set your team's main or secondary clan")(
            app_commands.describe(
                clan_type="Main or secondary clan",
                clan_tag="CoC clan tag"
            )(
            app_commands.choices(clan_type=[
                app_commands.Choice(name="Main", value="main"),
                app_commands.Choice(name="Secondary", value="secondary"),
            ])(team_setclan)
            )
        )
        self.group.command(name="setlanguage", description="Set your team's language")(
            app_commands.describe(
                language="Team language (e.g. English, Spanish)"
            )(team_setlanguage)
        )
        self.group.command(name="settimezone", description="Set your team's timezone")(
            app_commands.describe(
                timezone="Team timezone (e.g. UTC+5:30)"
            )(team_settimezone)
        )
        self.group.command(name="setrep", description="Set team representative 1 or 2")(
            app_commands.describe(
                user="The representative to assign",
                slot="Rep slot (1 or 2)"
            )(team_setrep)
        )
        self.group.command(name="addlogo", description="Upload your team logo")(
            app_commands.describe(
                logo="Logo image file",
                team_code="Team code (only needed outside an application channel)"
            )(team_addlogo)
        )
        self.group.command(name="addplayer", description="Add a player to the team roster")(
            app_commands.describe(
                tag="Player tag (e.g. #ABC123)"
            )(team_addplayer)
        )
        self.group.command(name="delplayer", description="Remove a player from the team roster")(
            app_commands.describe(
                tag="Player tag to remove"
            )(team_delplayer)
        )
        self.group.command(name="show", description="Preview your team application")(
            team_show
        )
        self.group.command(name="complete", description="Mark your application as ready for review")(
            team_complete
        )
        self.group.command(name="withdraw", description="Withdraw your team application")(
            team_withdraw
        )
        self.group.command(name="accept", description="Accept a team application")(
            team_accept
        )
        self.group.command(name="reject", description="Reject a team application")(
            app_commands.describe(
                reason="Reason for rejection"
            )(team_reject)
        )
        self.group.command(name="setup", description="Edit an accepted team's details")(
            app_commands.describe(
                division="Division code",
                code="Team code"
            )(team_setup)
        )
        self.group.command(name="info", description="View team information")(
            app_commands.describe(
                division="Division code",
                code="Team code (optional — omit to browse all teams)"
            )(team_info)
        )
        self.group.command(name="deletechannels", description="Delete all application channels for a division")(
            app_commands.describe(
                division="Division code"
            )(team_deletechannels)
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("team")


async def setup(bot):
    await bot.add_cog(Team(bot))
