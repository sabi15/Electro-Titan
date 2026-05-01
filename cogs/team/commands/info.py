import discord
from database.db import get_pool
from cogs.dev.utils import check_access
from cogs.team.utils import get_division_by_code


class TeamSelectView(discord.ui.View):
    def __init__(self, teams, division_code):
        super().__init__(timeout=60)
        self.teams = teams
        self.division_code = division_code
        self.page = 0
        self.per_page = 10
        self._update_select()

    def _update_select(self):
        self.clear_items()
        start = self.page * self.per_page
        page_teams = self.teams[start:start + self.per_page]

        options = [
            discord.SelectOption(label=f"{t['team_name']} ({t['team_code']})", value=t['team_code'])
            for t in page_teams
        ]
        select = discord.ui.Select(placeholder="Choose a team...", options=options)
        select.callback = self._on_select
        self.add_item(select)

        if self.page > 0:
            prev_btn = discord.ui.Button(label="◀ Prev", style=discord.ButtonStyle.secondary)
            prev_btn.callback = self._prev
            self.add_item(prev_btn)

        if start + self.per_page < len(self.teams):
            next_btn = discord.ui.Button(label="Next ▶", style=discord.ButtonStyle.secondary)
            next_btn.callback = self._next
            self.add_item(next_btn)

    async def _on_select(self, interaction: discord.Interaction):
        team_code = interaction.data['values'][0]
        pool = await get_pool()
        gid = str(interaction.guild_id)

        team = await pool.fetchrow(
            "SELECT * FROM teams WHERE guild_id=$1 AND division_code=$2 AND team_code=$3",
            gid, self.division_code, team_code
        )
        if not team:
            await interaction.response.send_message(embed=discord.Embed(
                description="❌ Team not found.",
                color=0xe74c3c
            ))
            return

        embed = discord.Embed(
            title=f"Team Information — {team['team_name']}",
            color=0x2b2d31
        )
        embed.add_field(name="🏷️ Code", value=f"`{team['team_code']}`", inline=True)
        embed.add_field(name="📊 Status", value=team['status'].capitalize(), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Rep 1
        rep1 = f"<@{team['rep_id']}>" if team['rep_id'] else "Not set"
        embed.add_field(name="👤 Rep 1", value=rep1, inline=True)

        # Rep 2
        rep2 = f"<@{team['rep2_id']}>" if team['rep2_id'] else "Not set"
        embed.add_field(name="👤 Rep 2", value=rep2, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Main clan
        main_value = "Not set"
        if team['main_clan']:
            try:
                clan = await interaction.client.coc_client.get_clan(team['main_clan'])
                link = f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={team['main_clan'].replace('#','')}"
                main_value = f"[{clan.name}]({link}) — Lv.**{clan.level}**"
                embed.set_thumbnail(url=clan.badge.url)
            except Exception:
                main_value = f"`{team['main_clan']}`"
        embed.add_field(name="🏰 Main Clan", value=main_value, inline=True)

        # Secondary clan
        if team['secondary_clan']:
            sec_value = "Not set"
            try:
                clan2 = await interaction.client.coc_client.get_clan(team['secondary_clan'])
                link2 = f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={team['secondary_clan'].replace('#','')}"
                sec_value = f"[{clan2.name}]({link2}) — Lv.**{clan2.level}**"
            except Exception:
                sec_value = f"`{team['secondary_clan']}`"
            embed.add_field(name="🏰 Secondary Clan", value=sec_value, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="🕐 Timezone", value=team['timezone'] or "Not set", inline=True)
        embed.add_field(name="🌐 Language", value=team['language'] or "Not set", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        if team['logo_url']:
            embed.set_thumbnail(url=team['logo_url'])

        embed.set_footer(text=f"{self.division_code}")

        # Disable the select after use
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=embed)

    async def _prev(self, interaction: discord.Interaction):
        self.page -= 1
        self._update_select()
        await interaction.response.edit_message(view=self)

    async def _next(self, interaction: discord.Interaction):
        self.page += 1
        self._update_select()
        await interaction.response.edit_message(view=self)


async def team_info(interaction: discord.Interaction, division: str, code: str = None):
    if not await check_access(interaction, "team"):
        return
    await interaction.response.defer()
    pool = await get_pool()
    gid = str(interaction.guild_id)
    division = division.strip().upper()

    div = await get_division_by_code(gid, division)
    if not div:
        await interaction.followup.send(embed=discord.Embed(
            description="❌ Division not found.",
            color=0xe74c3c
        ))
        return

    if code:
        code = code.strip().upper()
        team = await pool.fetchrow(
            "SELECT * FROM teams WHERE guild_id=$1 AND division_code=$2 AND team_code=$3 AND status='active'",
            gid, division, code
        )
        if not team:
            await interaction.followup.send(embed=discord.Embed(
                description=f"❌ Team **{code}** not found in **{division}**.",
                color=0xe74c3c
            ))
            return

        embed = discord.Embed(
            title=f"Team Information — {team['team_name']}",
            color=0x2b2d31
        )
        embed.add_field(name="🏷️ Code", value=f"`{team['team_code']}`", inline=True)
        embed.add_field(name="📊 Status", value=team['status'].capitalize(), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        rep1 = f"<@{team['rep_id']}>" if team['rep_id'] else "Not set"
        embed.add_field(name="👤 Rep 1", value=rep1, inline=True)
        rep2 = f"<@{team['rep2_id']}>" if team['rep2_id'] else "Not set"
        embed.add_field(name="👤 Rep 2", value=rep2, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        main_value = "Not set"
        if team['main_clan']:
            try:
                clan = await interaction.client.coc_client.get_clan(team['main_clan'])
                link = f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={team['main_clan'].replace('#','')}"
                main_value = f"[{clan.name}]({link}) — Lv.**{clan.level}**"
            except Exception:
                main_value = f"`{team['main_clan']}`"
        embed.add_field(name="🏰 Main Clan", value=main_value, inline=True)

        if team['secondary_clan']:
            sec_value = "Not set"
            try:
                clan2 = await interaction.client.coc_client.get_clan(team['secondary_clan'])
                link2 = f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={team['secondary_clan'].replace('#','')}"
                sec_value = f"[{clan2.name}]({link2}) — Lv.**{clan2.level}**"
            except Exception:
                sec_value = f"`{team['secondary_clan']}`"
            embed.add_field(name="🏰 Secondary Clan", value=sec_value, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="🕐 Timezone", value=team['timezone'] or "Not set", inline=True)
        embed.add_field(name="🌐 Language", value=team['language'] or "Not set", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        if team['logo_url']:
            embed.set_thumbnail(url=team['logo_url'])

        embed.set_footer(text=division)
        await interaction.followup.send(embed=embed)
        return

    # No code — show paginated selector
    teams = await pool.fetch(
        "SELECT * FROM teams WHERE guild_id=$1 AND division_code=$2 AND status='active' ORDER BY team_name",
        gid, division
    )
    if not teams:
        await interaction.followup.send(embed=discord.Embed(
            description=f"❌ No accepted teams found in **{division}**.",
            color=0xe74c3c
        ))
        return

    view = TeamSelectView(list(teams), division)
    await interaction.followup.send(
        embed=discord.Embed(
            description=f"**{division}** — Select a team to view:",
            color=0x2b2d31
        ),
        view=view
    )
