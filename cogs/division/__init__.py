from discord.ext import commands as ext_commands
from discord import app_commands
from cogs.division.commands.create import division_create
from cogs.division.commands.deactivate import division_deactivate
from cogs.division.commands.delete import division_delete
from cogs.division.commands.setup import division_setup
from cogs.division.commands.showsetup import division_showsetup
from cogs.division.commands.addgroup import division_addgroup
from cogs.division.commands.delgroup import division_delgroup
from cogs.division.commands.draw import division_draw
from cogs.division.commands.groups import division_groups
from cogs.division.commands.info import division_info
from cogs.division.commands.setlogo import division_setlogo
from cogs.division.commands.newseason import division_newseason
from cogs.division.commands.participants import division_participants
from cogs.division.commands.list import division_list


class Division(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="division", description="Division management commands")

        self.group.command(name="create", description="Create a new division")(
            app_commands.describe(
                division_name="Name of the division",
                league_code="Code of the league this division belongs to",
                season="Starting season number (e.g. 1)",
                transaction_log_channel="Channel where transactions will be logged",
                rep_role="Role assigned to team representatives"
            )(division_create)
        )
        self.group.command(name="deactivate", description="Toggle a division active/inactive")(
            app_commands.describe(
                code="Code of the division to toggle"
            )(division_deactivate)
        )
        self.group.command(name="delete", description="Permanently delete a division")(
            app_commands.describe(
                code="Code of the division to delete"
            )(division_delete)
        )
        self.group.command(name="setup", description="Configure division settings")(
            app_commands.describe(
                division="Code of the division to configure"
            )(division_setup)
        )
        self.group.command(name="showsetup", description="View all configured settings for a division")(
            app_commands.describe(
                division="Code of the division to view settings for"
            )(division_showsetup)
        )
        self.group.command(name="addgroup", description="Add a group to a schedule")(
            app_commands.describe(
                division="Code of the division",
                schedule_name="Name of the schedule to add the group to",
                group_name="Name of the group (e.g. Group A)",
                team_codes="Comma-separated team codes (e.g. TSM,GBS1,NRG)"
            )(division_addgroup)
        )
        self.group.command(name="delgroup", description="Delete a group from a schedule")(
            app_commands.describe(
                division="Code of the division",
                schedule_name="Name of the schedule",
                group_name="Name of the group to delete"
            )(division_delgroup)
        )
        self.group.command(name="draw", description="Randomly assign participants into groups")(
            app_commands.describe(
                division="Code of the division",
                schedule_name="Name of the schedule to draw for",
                groups="Number of groups to create",
                by_timezone="Whether to group teams by timezone before drawing"
            )(division_draw)
        )
        self.group.command(name="groups", description="View all groups in a division")(
            app_commands.describe(
                division="Code of the division to view groups for"
            )(division_groups)
        )
        self.group.command(name="info", description="View details of a division")(
            app_commands.describe(
                code="Code of the division to view"
            )(division_info)
        )
        self.group.command(name="setlogo", description="Set the logo for a division")(
            app_commands.describe(
                division="Code of the division",
                logo="Direct image URL for the division logo"
            )(division_setlogo)
        )
        self.group.command(name="newseason", description="Archive current season and start fresh")(
            app_commands.describe(
                code="Code of the division to start a new season for"
            )(division_newseason)
        )
        self.group.command(name="participants", description="View all participants in a division")(
            app_commands.describe(
                division="Code of the division to view participants for"
            )(division_participants)
        )
        self.group.command(name="list", description="List all active divisions in this server")(
            division_list
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("division")


async def setup(bot):
    await bot.add_cog(Division(bot))
