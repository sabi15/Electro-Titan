import discord
from discord import app_commands
from database.db import get_pool
from config import VALID_PERMS, BOT_DEV_ID


async def addperms(interaction: discord.Interaction, role: discord.Role, perm: str):
    if interaction.user.id != BOT_DEV_ID:
        await interaction.response.send_message("❌ Dev only.",)
        return

    pool = await get_pool()
    gid = str(interaction.guild_id)

    try:
        await pool.execute(
            """INSERT INTO perm_assignments (guild_id, role_id, permission)
               VALUES ($1, $2, $3)
               ON CONFLICT DO NOTHING""",
            gid, str(role.id), perm
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ DB error: {e}",)
        return

    embed = discord.Embed(
        title="✅ Permission Added",
        color=0x2ecc71
    )
    embed.add_field(name="Role", value=role.mention, inline=True)
    embed.add_field(name="Permission", value=f"`{perm}`", inline=True)
    embed.add_field(name="Server", value=interaction.guild.name, inline=False)
    await interaction.response.send_message(embed=embed)


addperms.__discord_app_commands_param_description__ = {}
for _perm in VALID_PERMS:
    pass

def setup_choices(cmd):
    cmd = app_commands.describe(
        role="The role to assign the permission to",
        perm="The permission to assign"
    )(cmd)
    cmd = app_commands.choices(perm=[
        app_commands.Choice(name=p, value=p) for p in VALID_PERMS
    ])(cmd)
    return cmd

addperms = setup_choices(addperms)
