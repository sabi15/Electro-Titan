import discord
from discord import app_commands
from database.db import get_pool
from utils.emojis import get_th_emoji
from cogs.acc.utils import maybe_send_invite
from datetime import timezone


@app_commands.describe(
    tag="A CoC player tag to check history for",
    user="A Discord user to check history for"
)
async def history(interaction: discord.Interaction, tag: str = None, user: discord.Member = None):
    await interaction.response.defer()

    if tag is None and user is None:
        user = interaction.user

    pool = await get_pool()

    if tag:
        if not tag.startswith("#"):
            tag = "#" + tag
        tag = tag.upper()

        rows = await pool.fetch(
            """
            SELECT discord_id, tag, ign, th_level, action, actioned_at
            FROM acc_history
            WHERE tag = $1
            ORDER BY actioned_at ASC
            """,
            tag
        )

        if not rows:
            embed = discord.Embed(
                description=f"❌ No history found for tag `{tag}`.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return

        latest = rows[-1]
        th_emoji = get_th_emoji(latest["th_level"])

        embed = discord.Embed(
            title=f"Link History of {latest['ign']}",
            color=discord.Color.blurple()
        )
        lines = _build_tag_history_lines(rows, interaction.guild)
        embed.description = "\n".join(lines) if lines else "No events recorded."
        embed.set_footer(text=f"{len(rows)} event(s)")
        await interaction.followup.send(embed=embed)

    else:
        rows = await pool.fetch(
            """
            SELECT tag, ign, th_level, action, actioned_at
            FROM acc_history
            WHERE discord_id = $1
            ORDER BY actioned_at ASC
            """,
            user.id
        )

        if not rows:
            embed = discord.Embed(
                description=f"❌ No history found for {user.mention}.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"Acc Link History of {user.display_name}",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        lines = _build_user_history_lines(rows)
        embed.description = "\n".join(lines) if lines else "No events recorded."
        embed.set_footer(text=f"{len(rows)} event(s)")
        await interaction.followup.send(embed=embed)

    invite = await maybe_send_invite(interaction.user.id)
    if invite:
        await interaction.followup.send(invite)


def _build_user_history_lines(rows) -> list[str]:
    lines = []
    pending: dict[str, dict] = {}

    for row in rows:
        key = row["tag"]
        th_emoji = get_th_emoji(row["th_level"])
        ign = row["ign"]
        ts_unix = int(row["actioned_at"].replace(tzinfo=timezone.utc).timestamp())

        if row["action"] == "claimed":
            pending[key] = {
                "ts_unix": ts_unix,
                "th_emoji": th_emoji,
                "ign": ign,
                "tag": row["tag"]
            }
        elif row["action"] == "removed":
            if key in pending:
                start_unix = pending.pop(key)["ts_unix"]
                lines.append(
                    f"{th_emoji} **{ign}** (`{row['tag']}`) — <t:{start_unix}:D> to <t:{ts_unix}:D>"
                )
            else:
                lines.append(
                    f"{th_emoji} **{ign}** (`{row['tag']}`) — *(unknown start)* to <t:{ts_unix}:D>"
                )

    for key, data in pending.items():
        lines.append(
            f"{data['th_emoji']} **{data['ign']}** (`{data['tag']}`) — <t:{data['ts_unix']}:D> to **present**"
        )

    return lines


def _build_tag_history_lines(rows, guild: discord.Guild) -> list[str]:
    lines = []
    pending: dict[int, int] = {}

    for row in rows:
        discord_id = row["discord_id"]
        ts_unix = int(row["actioned_at"].replace(tzinfo=timezone.utc).timestamp())

        if row["action"] == "claimed":
            pending[discord_id] = ts_unix
        elif row["action"] == "removed":
            if discord_id in pending:
                start_unix = pending.pop(discord_id)
                member = guild.get_member(discord_id)
                user_display = member.mention if member else f"<@{discord_id}>"
                lines.append(
                    f"<t:{start_unix}:D> to <t:{ts_unix}:D> — {user_display}"
                )
            else:
                member = guild.get_member(discord_id)
                user_display = member.mention if member else f"<@{discord_id}>"
                lines.append(
                    f"*(unknown start)* to <t:{ts_unix}:D> — {user_display}"
                )

    for discord_id, start_unix in pending.items():
        member = guild.get_member(discord_id)
        user_display = member.mention if member else f"<@{discord_id}>"
        lines.append(
            f"<t:{start_unix}:D> to **present** — {user_display}"
        )

    return lines
