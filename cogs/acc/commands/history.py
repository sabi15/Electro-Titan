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
            SELECT discord_id, ign, th_level, action, actioned_at
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
            title=f"Account History — {th_emoji} {latest['ign']} ({tag})",
            color=discord.Color.blurple()
        )
        lines = _build_history_lines(rows, by="tag")
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
            title=f"Account History — {user.display_name}",
            color=discord.Color.blurple()
        )
        lines = _build_history_lines(rows, by="user")
        embed.description = "\n".join(lines) if lines else "No events recorded."
        embed.set_footer(text=f"{len(rows)} event(s)")
        await interaction.followup.send(embed=embed)

    invite = await maybe_send_invite(interaction.user.id)
    if invite:
        await interaction.followup.send(invite)


def _build_history_lines(rows, by: str) -> list[str]:
    lines = []
    pending: dict[str, dict] = {}

    for row in rows:
        key = row["tag"]
        th_emoji = get_th_emoji(row["th_level"])
        ign = row["ign"]
        ts_unix = int(row["actioned_at"].replace(tzinfo=timezone.utc).timestamp())

        if row["action"] == "claimed":
            pending[key] = {"ts_unix": ts_unix, "th_emoji": th_emoji, "ign": ign, "tag": row["tag"]}
        elif row["action"] == "removed":
            if key in pending:
                start_unix = pending.pop(key)["ts_unix"]
                entry_tag = f" (`{row['tag']}`)" if by == "user" else ""
                lines.append(f"{th_emoji} **{ign}**{entry_tag} — <t:{start_unix}:D> to <t:{ts_unix}:D>")
            else:
                entry_tag = f" (`{row['tag']}`)" if by == "user" else ""
                lines.append(f"{th_emoji} **{ign}**{entry_tag} — *(unknown start)* to <t:{ts_unix}:D>")

    for key, data in pending.items():
        entry_tag = f" (`{data['tag']}`)" if by == "user" else ""
        lines.append(f"{data['th_emoji']} **{data['ign']}**{entry_tag} — <t:{data['ts_unix']}:D> to **present**")

    return lines
