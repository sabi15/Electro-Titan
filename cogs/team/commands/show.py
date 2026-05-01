import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_app_by_channel, get_division_setting, get_division_by_code
from utils.emojis import get_th_emoji


async def team_show(interaction: discord.Interaction):
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

    team = await pool.fetchrow(
        "SELECT * FROM teams WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
        gid, app['division_code'], app['team_code']
    )
    roster = await pool.fetch(
        "SELECT player_tag FROM rosters WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
        gid, app['division_code'], app['team_code']
    )

    div = await get_division_by_code(gid, app['division_code'])
    min_roster = await get_division_setting(div['id'], 'min_roster')
    max_roster = await get_division_setting(div['id'], 'max_roster')
    require_secondary = await get_division_setting(div['id'], 'allow_secondary_clan')
    team_requirements = await get_division_setting(div['id'], 'team_requirements')

    issues = []
    roster_count = len(roster)

    if min_roster and roster_count < int(min_roster):
        issues.append(f"Roster too small: **{roster_count}**/{min_roster}")
    if not team or not team['main_clan']:
        issues.append("Main clan is missing")
    if require_secondary == 'true' and (not team or not team['secondary_clan']):
        issues.append("Secondary clan is missing")
    if not team or not team['timezone']:
        issues.append("Timezone is missing")
    if not team or not team['language']:
        issues.append("Language is missing")
    if not team or not team['logo_url']:
        issues.append("Logo is missing")

    desc_parts = []
    if team_requirements:
        desc_parts.append(f"{team_requirements}\n")
    desc_parts.append("\n".join(f"⚠️ {i}" for i in issues) if issues else "✅ All requirements met!")

    embed = discord.Embed(
        title=app['team_name'],
        description="\n".join(desc_parts),
        color=0xe67e22 if issues else 0x2ecc71
    )

    # Main clan
    main_clan_value = "Not set"
    main_clan_badge = None
    if team and team['main_clan']:
        try:
            clan = await interaction.client.coc_client.get_clan(team['main_clan'])
            link = f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={team['main_clan'].replace('#','')}"
            main_clan_value = f"[{clan.name}]({link}) — Lv.**{clan.level}**"
            main_clan_badge = clan.badge.url
        except Exception:
            main_clan_value = f"`{team['main_clan']}`"
    embed.add_field(name="🏰 Main Clan", value=main_clan_value, inline=True)

    # Secondary clan
    if require_secondary == 'true' or (team and team['secondary_clan']):
        sec_value = "Not set"
        if team and team['secondary_clan']:
            try:
                clan2 = await interaction.client.coc_client.get_clan(team['secondary_clan'])
                link2 = f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={team['secondary_clan'].replace('#','')}"
                sec_value = f"[{clan2.name}]({link2}) — Lv.**{clan2.level}**"
            except Exception:
                sec_value = f"`{team['secondary_clan']}`"
        embed.add_field(name="🏰 Secondary Clan", value=sec_value, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
    else:
        embed.add_field(name="\u200b", value="\u200b", inline=True)

    # Rep 1
    rep1_value = f"<@{app['rep_id']}>" if app['rep_id'] else "Not set"
    embed.add_field(name="👤 Rep 1", value=rep1_value, inline=True)

    # Rep 2
    rep2_value = f"<@{team['rep2_id']}>" if team and team['rep2_id'] else "Not set"
    embed.add_field(name="👤 Rep 2", value=rep2_value, inline=True)

    embed.add_field(name="🏷️ Team Code", value=f"`{app['team_code']}`", inline=True)
    embed.add_field(name="🕐 Timezone", value=team['timezone'] if team and team['timezone'] else "Not set", inline=True)
    embed.add_field(name="🌐 Language", value=team['language'] if team and team['language'] else "Not set", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    # Roster by TH
    if roster:
        th_groups = {}
        for r in roster:
            try:
                player = await interaction.client.coc_client.get_player(r['player_tag'])
                th = player.town_hall
                if th not in th_groups:
                    th_groups[th] = []
                th_groups[th].append(f"{player.name} ({player.tag})")
            except Exception:
                th_groups.setdefault(0, []).append(f"Unknown ({r['player_tag']})")

        for th_level in sorted(th_groups.keys(), reverse=True):
            players = th_groups[th_level]
            th_emoji = get_th_emoji(th_level)
            field_value = "```\n" + "\n".join(players) + "\n```"
            if len(field_value) > 1024:
                field_value = field_value[:1020] + "\n```"
            embed.add_field(name=f"{th_emoji} TH{th_level} ({len(players)})", value=field_value, inline=False)
    else:
        embed.add_field(name="👥 Roster", value="No players added yet.", inline=False)

    if team and team['logo_url']:
        embed.set_thumbnail(url=team['logo_url'])
    elif main_clan_badge:
        embed.set_thumbnail(url=main_clan_badge)

    embed.set_footer(text=f"{app['division_code']} • Status: {app['status'].capitalize()}")
    await interaction.followup.send(embed=embed)
