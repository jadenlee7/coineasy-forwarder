"""
CoinEasy Channel Forwarder Bot
Telethon user-account based forwarder.

Listens to source channels (Wallet V KR, Squid KR, Yellow KR) and forwards
new messages to @coiniseasy, preserving the original source attribution.
"""

import asyncio
import logging
import os
import sys
from collections import defaultdict

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, AuthKeyDuplicatedError
from telethon.sessions import StringSession

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("forwarder")

# ---------- Config ----------
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELETHON_SESSION_STRING")

# Source channels
SOURCE_CHANNELS = [
    "WalletvKR",
    "squid_kor_update",
    "YellowKorea_ann",
]

# Destination = CoinEasy announcement channel (@coiniseasy)
DESTINATION = os.getenv("COINEASY_ANNOUNCE_CHANNEL", "coiniseasy")

# Validation
if not API_ID or not API_HASH:
    logger.error("TELEGRAM_API_ID / TELEGRAM_API_HASH must be set")
    sys.exit(1)

if not SESSION_STRING:
    logger.error("TELETHON_SESSION_STRING must be set (run generate_session.py locally first)")
    sys.exit(1)

SESSION_STRING = SESSION_STRING.strip()

API_ID = int(API_ID)

# Convert numeric ID if applicable
try:
    DESTINATION = int(DESTINATION)
except (TypeError, ValueError):
    pass

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------- Album buffering ----------
# Telegram delivers album posts as separate messages that share a `grouped_id`.
# We collect them briefly so the whole album is forwarded as a single post.
ALBUM_FLUSH_DELAY = 2.5  # seconds to wait for sibling album messages
_album_buffers: dict[int, list] = defaultdict(list)
_album_tasks: dict[int, asyncio.Task] = {}
_album_lock = asyncio.Lock()


async def _forward_messages(messages, source_name):
    """Forward one or more messages (single post or album) to DESTINATION."""
    messages = sorted(messages, key=lambda m: m.id)
    first = messages[0]
    try:
        await client.forward_messages(
            entity=DESTINATION,
            messages=messages,
            from_peer=await first.get_input_chat(),
        )
        ids = ", ".join(str(m.id) for m in messages)
        kind = "album" if len(messages) > 1 else "msg"
        logger.info(f"✓ Forwarded {kind} [{ids}] from @{source_name}")
    except Exception as fwd_err:
        logger.warning(
            f"forward_messages failed for @{source_name}: {fwd_err}. "
            f"Falling back to send_message."
        )
        prefix = f"[{source_name}]\n"
        if len(messages) > 1:
            files = [m.media for m in messages if m.media is not None]
            caption = prefix + (
                next((m.text for m in messages if m.text), "") or ""
            )
            await client.send_file(
                entity=DESTINATION,
                file=files,
                caption=caption,
            )
            logger.info(
                f"✓ Sent album [{', '.join(str(m.id) for m in messages)}] "
                f"from @{source_name} as new message (fallback)"
            )
        else:
            msg = messages[0]
            if msg.media:
                await client.send_message(
                    entity=DESTINATION,
                    message=prefix + (msg.text or ""),
                    file=msg.media,
                )
            else:
                await client.send_message(
                    entity=DESTINATION,
                    message=prefix + (msg.text or ""),
                )
            logger.info(
                f"✓ Sent msg {msg.id} from @{source_name} as new message (fallback)"
            )


async def _flush_album(group_id: int, source_name: str):
    """Wait briefly for more album siblings, then forward the collected batch."""
    try:
        await asyncio.sleep(ALBUM_FLUSH_DELAY)
        async with _album_lock:
            messages = _album_buffers.pop(group_id, [])
            _album_tasks.pop(group_id, None)
        if not messages:
            return
        try:
            await _forward_messages(messages, source_name)
        except FloodWaitError as e:
            logger.warning(f"FloodWait: sleeping {e.seconds}s")
            await asyncio.sleep(e.seconds + 1)
        except Exception as e:
            logger.exception(f"Forward failed: {e}")
    except asyncio.CancelledError:
        raise


@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    """Forward every new message from source channels to destination."""
    try:
        chat = await event.get_chat()
        source_name = getattr(chat, "username", None) or getattr(chat, "title", "unknown")

        group_id = getattr(event.message, "grouped_id", None)
        if group_id:
            async with _album_lock:
                _album_buffers[group_id].append(event.message)
                if group_id not in _album_tasks:
                    _album_tasks[group_id] = asyncio.create_task(
                        _flush_album(group_id, source_name)
                    )
            return

        await _forward_messages([event.message], source_name)

    except FloodWaitError as e:
        logger.warning(f"FloodWait: sleeping {e.seconds}s")
        await asyncio.sleep(e.seconds + 1)
    except Exception as e:
        logger.exception(f"Forward failed: {e}")


async def main():
    try:
        await client.start()
    except AuthKeyDuplicatedError:
        logger.error(
            "SESSION EXPIRED: The session string was used from multiple "
            "IP addresses and is now invalid. Please run generate_session.py "
            "to create a NEW session string and update TELETHON_SESSION_STRING "
            "in Railway environment variables."
        )
        sys.exit(1)

    me = await client.get_me()
    logger.info(f"Logged in as {me.username or me.first_name} (id={me.id})")
    logger.info(f"Destination: {DESTINATION}")

    logger.info("Verifying channel access...")
    for ch in SOURCE_CHANNELS:
        try:
            entity = await client.get_entity(ch)
            logger.info(f"  ✓ source @{ch} -> {entity.title}")
        except Exception as e:
            logger.error(f"  ✗ Cannot resolve source @{ch}: {e}")

    try:
        dest_entity = await client.get_entity(DESTINATION)
        logger.info(f"  ✓ destination -> {dest_entity.title}")
    except Exception as e:
        logger.error(f"  ✗ Cannot resolve destination {DESTINATION}: {e}")
        logger.error("    Make sure your account has post permissions on this channel")

    logger.info("Listening for new messages...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
