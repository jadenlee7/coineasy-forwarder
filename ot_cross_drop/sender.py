"""Send approved messages to global OriginTrail channels."""
import asyncio
import logging

from .config import SEND_DELAY_SECONDS, TARGET_CHANNELS

logger = logging.getLogger(__name__)


async def send_to_global(client, message: str) -> list[tuple[str, int]]:
    """Send `message` to each target channel.

    Returns [(channel, msg_id), ...]. msg_id is -1 on failure.
    """
    results: list[tuple[str, int]] = []
    for channel in TARGET_CHANNELS:
        try:
            sent = await client.send_message(channel, message, link_preview=True)
            results.append((channel, sent.id))
            logger.info("[ot-cross-drop] sent to %s: msg_id=%s", channel, sent.id)
        except Exception as e:
            logger.error("[ot-cross-drop] failed to send to %s: %s", channel, e)
            results.append((channel, -1))
        await asyncio.sleep(SEND_DELAY_SECONDS)
    return results
