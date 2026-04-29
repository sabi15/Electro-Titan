from .commands.create import DivisionCreate
from .commands.delete import DivisionDelete
from .commands.deactivate import DivisionDeactivate
from .commands.info import DivisionInfo
from .commands.setlogo import DivisionSetLogo
from .commands.newseason import DivisionNewSeason
from .commands.setup import DivisionSetup
from .commands.addgroup import DivisionAddGroup
from .commands.delgroup import DivisionDelGroup
from .commands.draw import DivisionDraw
from .commands.groups import DivisionGroups
from .commands.participants import DivisionParticipants

class Division(
    DivisionCreate,
    DivisionDelete,
    DivisionDeactivate,
    DivisionInfo,
    DivisionSetLogo,
    DivisionNewSeason,
    DivisionSetup,
    DivisionAddGroup,
    DivisionDelGroup,
    DivisionDraw,
    DivisionGroups,
    DivisionParticipants,
    name="division"
):
    pass

async def setup(bot):
    await bot.add_cog(Division(bot))
