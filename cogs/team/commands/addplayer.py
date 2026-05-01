import discord
import coc
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, is_authorized, get_division_setting, get_division_by_code
from utils.helpers import normalize_tag


async def team_addplayer(interaction: discord.Interaction, tag: str):
    if not await check_access(interaction, "team"):
        return
    await interaction.response.defer()
    pool = await get_pool()
    gid = str(interaction.guild_id)

    app = await get_app_by_channel(str(interaction.channel_id), gid)
    if not app:
        await interaction.followup.send(embed=discord.Embed(
            description="❌ Use this command inside an application channel.",
            color=0xe74c3c
        ))
        return

    if not await is_authorized(interaction, app):
        await interaction.followup.send(embed=discord.Embed(
            description="❌ You are not authorized to use this command here.",
            color=0xe74c3c
        ))
        return

    tag = normalize_tag(tag)
    div = await get_division_by_code(gid, app['division_code'])

    # Required claims check
    required_claims = await get_division_setting(div['id'], 'required_claims')
    claimed_by = None
    if required_claims and required_claims.lower() == 'true':
        claim = await pool.fetchrow(
            "SELECT discord_id FROM acc_accounts WHERE tag=$1",
            tag
        )
        if not claim:
            await interaction.followup.send(embed=discord.Embed(
                description=f"❌ `{tag}` has not been claimed via `/acc`. Claims are required in this division.",
                color=0xe74c3c
            ))
            return
        claimed_by = str(claim['discord_id'])

        # Max accounts per user check
        max_accounts = await get_division_setting(div['id'], 'max_accounts_per_user')
        if max_accounts:
            user_count = await pool.fetchval(
                "SELECT COUNT(*) FROM rosters WHERE guild_id=$1 AND division_code=$2 AND claimed_by=$3",
                gid, app['division_code'], claimed_by
            )
            if user_count >= int(max_accounts):
                await interaction.followup.send(embed=discord.Embed(
                    description=f"❌ That user already has the maximum number of accounts (**{max_accounts}**) in this division.",
                    color=0xe74c3c
                ))
                return

        # Dual player check
        allow_dual = await get_division_setting(div['id'], 'allow_dual')
        if not allow_dual or allow_dual.lower() != 'true':
            other_team = await pool.fetchrow(
                "SELECT team_code FROM rosters WHERE guild_id=$1 AND division_code=$2 AND claimed_by=$3 AND team_code!=$4",
                gid, app['division_code'], claimed_by, app['team_code']
            )
            if other_team:
                await interaction.followup.send(embed=discord.Embed(
                    description=f"❌ That user already has an account in team **{other_team['team_code']}**. Dual players are not allowed.",
                    color=0xe74c3c
                ))
                return

    # Check player not already in another team
    existing = await pool.fetchrow(
        "SELECT team_code FROM rosters WHERE guild_id=$1 AND division_code=$2 AND player_tag=$3",
        gid, app['division_code'], tag
    )
    if existing:
        await interaction.followup.send(embed=discord.Embed(
            description=f"❌ `{tag}` is already on team **{existing['team_code']}**.",
            color=0xe74c3c
        ))
        return

    # Max roster check
    max_roster = await get_division_setting(div['id'], 'max_roster')
    if max_roster:
        current_count = await pool.fetchval(
            "SELECT COUNT(*) FROM rosters WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
            gid, app['division_code'], app['team_code']
        )
        if current_count >= int(max_roster):
            await interaction.followup.send(embed=discord.Embed(
                description=f"❌ Roster is full. Maximum is **{max_roster}** players.",
                color=0xe74c3c
            ))
            return

    # Fetch player from CoC API
    try:
        player = await interaction.client.coc_client.get_player(tag)
    except coc.NotFound:
        await interaction.followup.send(embed=discord.Embed(
            description="❌ Player not found. Check the tag and try again.",
            color=0xe74c3c
        ))
        return
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(
            description=f"❌ CoC API error: {e}",
            color=0xe74c3c
        ))
        return

    await pool.execute(
        "INSERT INTO rosters (guild_id, division_code, team_code, player_tag, claimed_by) VALUES ($1,$2,$3,$4,$5)",
        gid, app['division_code'], app['team_code'], tag, claimed_by
    )

    from utils.emojis import get_th_emoji
    th_emoji = get_th_emoji(player.town_hall)
    await interaction.followup.send(embed=discord.Embed(
        description=f"✅ {th_emoji} **{player.name}** (`{player.tag}`) added to **{app['team_name']}**.",
        color=0x2ecc71
    ))
