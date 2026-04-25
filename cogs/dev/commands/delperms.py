import discord
from discord import app_commands
from database.db import get_pool
from config import VALID_PERMS, BOT_DEV_ID


async def delperms(interaction: discord.Interaction, role: discord.Role, perm: str):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    pool = await get_pool()
    gid = str(interaction.guild_id)

    result = await pool.execute(
        """DELETE FROM perm_assignments
           WHERE guild_id=$1 AND role_id=$2 AND permission=$3""",
        gid, str(role.id), perm
    )

    if result == "DELETE 0":
        await interaction.response.send_message(
            f"❌ That role doesn't have `{perm}`.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="✅ Permission Removed",
        color=0xe74c3c
    )
    embed.add_field(name="Role", value=role.mention, inline=True)
    embed.add_field(name="Permission", value=f"`{perm}`", inline=True)
    embed.add_field(name="Server", value=interaction.guild.name, inline=False)
    await interaction.response.send_message(embed=embed)


def setup_choices(cmd):
    cmd = app_commands.describe(
        role="The role to remove the permission from",
        perm="The permission to remove"
    )(cmd)
    cmd = app_commands.choices(perm=[
        app_commands.Choice(name=p, value=p) for p in VALID_PERMS
    ])(cmd)
    return cmd

delperms = setup_choices(delperms)
