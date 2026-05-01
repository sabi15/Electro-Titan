import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_division_by_code, get_division_setting

APP_CATEGORY_MAX = 45


async def team_register(interaction: discord.Interaction, division: str, team_name: str, team_code: str):
    if not await check_access(interaction, "team"):
        return
    await interaction.response.defer()
    pool = await get_pool()
    gid = str(interaction.guild_id)
    division = division.strip().upper()
    team_code = team_code.strip().upper()
    team_name = team_name.strip()

    div = await get_division_by_code(gid, division)
    if not div or div['status'] != 'active':
        await interaction.followup.send(embed=discord.Embed(
            description="❌ Division not found or inactive.",
            color=0xe74c3c
        ))
        return

    accept_apps = await get_division_setting(div['id'], 'accept_applications')
    if accept_apps and accept_apps.lower() == 'false':
        await interaction.followup.send(embed=discord.Embed(
            description="❌ Applications are currently closed for this division.",
            color=0xe74c3c
        ))
        return

    existing_code = await pool.fetchrow(
        "SELECT 1 FROM applications WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
        gid, division, team_code
    )
    if existing_code:
        await interaction.followup.send(embed=discord.Embed(
            description=f"❌ Team code **{team_code}** is already taken.",
            color=0xe74c3c
        ))
        return

    already_applied = await pool.fetchrow(
        "SELECT 1 FROM applications WHERE guild_id=$1 AND division_code=$2 AND rep_id=$3 AND status='pending'",
        gid, division, str(interaction.user.id)
    )
    if already_applied:
        await interaction.followup.send(embed=discord.Embed(
            description="❌ You already have a pending application in this division.",
            color=0xe74c3c
        ))
        return

    guild = interaction.guild
    category = None
    for cat in guild.categories:
        if cat.name.startswith(f"Apps-{division}") and len(cat.channels) < APP_CATEGORY_MAX:
            category = cat
            break

    if not category:
        existing_cats = [c for c in guild.categories if c.name.startswith(f"Apps-{division}")]
        cat_number = len(existing_cats) + 1
        category = await guild.create_category(
            f"Apps-{division}-{cat_number}",
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False)
            }
        )

    manage_roles = await pool.fetch(
        "SELECT role_id FROM perm_assignments WHERE guild_id=$1 AND permission='MANAGE_APPLICATIONS'",
        gid
    )

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True,
            read_message_history=True, manage_channels=True
        )
    }
    for row in manage_roles:
        role = guild.get_role(int(row['role_id']))
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )

    channel = await guild.create_text_channel(
        f"app-{team_code.lower()}",
        category=category,
        overwrites=overwrites
    )

    await pool.execute(
        """
        INSERT INTO applications (guild_id, division_code, team_code, team_name, channel_id, rep_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        gid, division, team_code, team_name, str(channel.id), str(interaction.user.id)
    )
    await pool.execute(
        """
        INSERT INTO teams (guild_id, division_code, team_code, team_name, rep_id)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (guild_id, division_code, team_code) DO NOTHING
        """,
        gid, division, team_code, team_name, str(interaction.user.id)
    )

    app_message = await get_division_setting(div['id'], 'app_message')
    description = app_message if app_message else (
        "> `/team setclan` — Set your main or secondary clan\n"
        "> `/team setlanguage` — Set your team language\n"
        "> `/team settimezone` — Set your team timezone\n"
        "> `/team setrep` — Change your team representative\n"
        "> `/team addlogo` — Upload your team logo\n"
        "> `/team addplayer` — Add a player to your roster\n"
        "> `/team delplayer` — Remove a player from your roster\n"
        "> `/team show` — Preview your application\n"
        "> `/team complete` — Submit your application\n"
        "> `/team withdraw` — Withdraw your application"
    )

    app_embed = discord.Embed(description=description, color=0x2b2d31)
    if div['logo_url']:
        app_embed.set_thumbnail(url=div['logo_url'])

    await channel.send(content=interaction.user.mention, embed=app_embed)
    await interaction.followup.send(embed=discord.Embed(
        description=f"✅ Application channel created: {channel.mention}",
        color=0x2ecc71
    ))
