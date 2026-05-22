"""coineasy-forwarder plugin: OT KR → global cross-drop with approval queue.

Usage in forwarder's main entrypoint:

    from telethon import TelegramClient
    from ot_cross_drop import register

    client = TelegramClient(...)
    register(client)         # plug in OT module
    client.start()
    client.run_until_disconnected()
"""
from .monitor import register

__all__ = ["register"]
