"""Listen for new posts in the Korean OT Telegram channel.

This module exports `register(client)` instead of owning a client itself —
it plugs into coineasy-forwarder's existing Telethon session.
"""
import logging
import re

from telethon import events

from .approval import enqueue_for_approval, register as register_approval
from .config import SOURCE_CHANNEL

logger = logging.getLogger(__name__)

X_URL_RE = re.compile(r"https?://(?:x\.com|twitter\.com)/[\w\d_]+/status/\d+")


def register(client):
    """Attach all OT cross-drop handlers to the host forwarder's client."""

    @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def on_new_kr_post(event):
        msg = event.message
        text = msg.text or ""

        x_link = None
        match = X_URL_RE.search(text)
        if match:
            x_link = match.group(0)
        elif (
            getattr(msg, "web_preview", None)
            and getattr(msg.web_preview, "url", None)
            and X_URL_RE.match(msg.web_preview.url)
        ):
            x_link = msg.web_preview.url

        tg_permalink = f"https://t.me/{SOURCE_CHANNEL.lstrip('@')}/{msg.id}"
        drop_link = x_link or tg_permalink

        logger.info(
            "[ot-cross-drop] KR post id=%s, x_link=%s, using=%s",
            msg.id, x_link, drop_link,
        )

        await enqueue_for_approval(
            client=client,
            kr_msg_id=msg.id,
            drop_link=drop_link,
            source_was_x=bool(x_link),
            preview_text=text[:200],
        )

    # Approval module also needs to register its callback/edit handlers
    register_approval(client)
    logger.info("[ot-cross-drop] registered, monitoring %s", SOURCE_CHANNEL)
