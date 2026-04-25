from database.db import get_pool
from config import ACC_INVITE_MESSAGE


async def maybe_send_invite(discord_id: int) -> str | None:
    pool = await get_pool()

    row = await pool.fetchrow(
        """
        INSERT INTO acc_usage (discord_id, use_count)
        VALUES ($1, 1)
        ON CONFLICT (discord_id) DO UPDATE
            SET use_count = acc_usage.use_count + 1
        RETURNING use_count
        """,
        discord_id
    )

    if row["use_count"] % 3 == 0:
        return ACC_INVITE_MESSAGE
    return None
