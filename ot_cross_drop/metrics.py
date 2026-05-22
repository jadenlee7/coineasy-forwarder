"""Capture engagement metrics on sent drops."""
import asyncio
import logging
from datetime import datetime, timezone

from .config import METRIC_INTERVALS, SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)

_supabase = None


def _sb():
    global _supabase
    if _supabase is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            logger.warning("[ot-cross-drop] supabase-py not installed")
            return None
    return _supabase


async def track_drop(client, item: dict, results: list[tuple[str, int]]) -> None:
    """Persist drop event and schedule metric captures."""
    sb = _sb()
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "kr_msg_id": item["kr_msg_id"],
        "drop_link": item["drop_link"],
        "drop_msg": item["drop_msg"],
        "sent_at": now,
        "targets": [
            {"channel": ch, "msg_id": mid}
            for ch, mid in results
            if mid > 0
        ],
    }

    if sb:
        try:
            sb.table("ot_cross_drops").insert(record).execute()
        except Exception as e:
            logger.error("[ot-cross-drop] persist drop failed: %s", e)
    else:
        logger.info("[ot-cross-drop] DROP_LOG: %s", record)

    for minutes in METRIC_INTERVALS:
        asyncio.create_task(_delayed_capture(client, item, results, minutes))


async def _delayed_capture(
    client,
    item: dict,
    results: list[tuple[str, int]],
    delay_minutes: int,
) -> None:
    await asyncio.sleep(delay_minutes * 60)

    snapshot: dict[str, dict] = {}
    for channel, msg_id in results:
        if msg_id < 0:
            continue
        try:
            msg = await client.get_messages(channel, ids=msg_id)
            if msg is None:
                continue
            snapshot[channel] = {
                "views": msg.views or 0,
                "forwards": msg.forwards or 0,
                "reactions": _sum_reactions(msg),
            }
        except Exception as e:
            logger.error("[ot-cross-drop] metric capture failed for %s/%s: %s",
                         channel, msg_id, e)

    record = {
        "kr_msg_id": item["kr_msg_id"],
        "interval_minutes": delay_minutes,
        "snapshot": snapshot,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }

    sb = _sb()
    if sb:
        try:
            sb.table("ot_cross_drop_metrics").insert(record).execute()
        except Exception as e:
            logger.error("[ot-cross-drop] persist metrics failed: %s", e)
    else:
        logger.info("[ot-cross-drop] METRICS @%dmin: %s", delay_minutes, record)


def _sum_reactions(msg) -> int:
    if not getattr(msg, "reactions", None) or not msg.reactions.results:
        return 0
    return sum(r.count for r in msg.reactions.results)
