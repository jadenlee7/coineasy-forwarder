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

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
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

API_ID = int(API_ID)

# Convert numeric ID if applicable
try:
    DESTINATION = int(DESTINATION)
except (TypeError, ValueError):
    pass

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    """Forward every new message from source channels to destination."""
    try:
        chat = await event.get_chat()
        source_name = getattr(chat, "username", None) or getattr(chat, "title", "unknown")

        try:
            await client.forward_messages(
                entity=DESTINATION,
                messages=event.message,
            )
            logger.info(f"✓ Forwarded msg {event.message.id} from @{source_name}")
        except Exception as fwd_err:
            logger.warning(
                f"forward_messages failed for @{source_name}: {fwd_err}. "
                f"Falling back to send_message."
            )
            prefix = f"[{source_name}]\n"
            msg = event.message

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

    except FloodWaitError as e:
        logger.warning(f"FloodWait: sleeping {e.seconds}s")
        await asyncio.sleep(e.seconds + 1)
    except Exception as e:
        logger.exception(f"Forward failed: {e}")


async def main():
    await client.start()
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
