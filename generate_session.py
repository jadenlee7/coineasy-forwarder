"""
Run this ONCE locally to generate TELETHON_SESSION_STRING.
Then copy the printed string into Railway env var.

Usage:
  export TELEGRAM_API_ID=...
  export TELEGRAM_API_HASH=...
  python generate_session.py
"""

import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n" + "=" * 60)
    print("TELETHON_SESSION_STRING:")
    print("=" * 60)
    print(client.session.save())
    print("=" * 60)
    print("\nCopy the string above and set it as TELETHON_SESSION_STRING")
    print("in your Railway environment variables.\n")
