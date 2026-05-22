"""Approval queue — registers handlers on the host client passed in."""
import logging

from telethon import Button, events

from .config import (
    ADMIN_USER_IDS,
    APPROVAL_CHAT_ID,
    AUTO_APPROVE,
    TARGET_CHANNELS,
)
from .template import render

logger = logging.getLogger(__name__)

pending: dict[str, dict] = {}
edit_waiting: dict[int, str] = {}


async def enqueue_for_approval(
    client,
    kr_msg_id: int,
    drop_link: str,
    source_was_x: bool,
    preview_text: str,
) -> None:
    """Render draft and send to admin chat (or auto-dispatch if enabled)."""
    drop_msg = render(drop_link)

    pending_id = f"otdrop_{kr_msg_id}"
    pending[pending_id] = {
        "kr_msg_id": kr_msg_id,
        "drop_link": drop_link,
        "source_was_x": source_was_x,
        "drop_msg": drop_msg,
    }

    if AUTO_APPROVE:
        logger.info("[ot-cross-drop] AUTO_APPROVE on, dispatching kr_msg_id=%s",
                    kr_msg_id)
        from .sender import send_to_global
        from .metrics import track_drop
        results = await send_to_global(client, drop_msg)
        await track_drop(client, pending[pending_id], results)
        pending.pop(pending_id, None)
        return

    source_label = "X link" if source_was_x else "TG fallback"
    preview = (
        f"📝 **[OT cross-drop] New KR post**  `id: {kr_msg_id}`\n\n"
        f"_Preview_: {preview_text}{'...' if len(preview_text) >= 200 else ''}\n"
        f"_Drop link_: {drop_link} ({source_label})\n\n"
        f"────────\n"
        f"**Draft for global channels:**\n\n"
        f"{drop_msg}\n"
        f"────────\n"
        f"Targets: {' + '.join(TARGET_CHANNELS)}"
    )

    buttons = [
        [
            Button.inline("✅ Approve & Send", f"otapprove:{pending_id}".encode()),
            Button.inline("✏️ Edit", f"otedit:{pending_id}".encode()),
        ],
        [Button.inline("❌ Reject", f"otreject:{pending_id}".encode())],
    ]

    await client.send_message(
        APPROVAL_CHAT_ID, preview, buttons=buttons, parse_mode="md",
    )


def register(client):
    """Attach callback + edit-reply handlers."""

    @client.on(events.CallbackQuery(pattern=b"^ot(approve|edit|reject):"))
    async def on_button(event):
        if event.sender_id not in ADMIN_USER_IDS:
            await event.answer("Not authorized", alert=True)
            return

        try:
            raw = event.data.decode()
            action, pending_id = raw.split(":", 1)
        except ValueError:
            return

        item = pending.get(pending_id)
        if not item:
            await event.answer("Item no longer pending", alert=True)
            return

        if action == "otapprove":
            from .sender import send_to_global
            from .metrics import track_drop

            await event.answer("Sending...")
            results = await send_to_global(client, item["drop_msg"])
            await event.edit(
                f"✅ Sent (kr_msg_id={item['kr_msg_id']})\n\n"
                + "\n".join(
                    f"• {ch}: {'msg_id=' + str(mid) if mid > 0 else 'FAILED'}"
                    for ch, mid in results
                )
            )
            await track_drop(client, item, results)
            pending.pop(pending_id, None)

        elif action == "otreject":
            await event.edit(f"❌ Rejected (kr_msg_id={item['kr_msg_id']})")
            pending.pop(pending_id, None)

        elif action == "otedit":
            edit_waiting[event.sender_id] = pending_id
            await event.answer(
                "Reply with your edited version in this chat.",
                alert=True,
            )

    @client.on(events.NewMessage(chats=APPROVAL_CHAT_ID))
    async def on_edit_reply(event):
        if event.sender_id not in ADMIN_USER_IDS:
            return
        pending_id = edit_waiting.get(event.sender_id)
        if not pending_id:
            return

        item = pending.get(pending_id)
        if not item:
            edit_waiting.pop(event.sender_id, None)
            return

        new_text = event.message.text or ""
        if not new_text.strip():
            return

        item["drop_msg"] = new_text
        edit_waiting.pop(event.sender_id, None)

        buttons = [
            [
                Button.inline("✅ Approve & Send", f"otapprove:{pending_id}".encode()),
                Button.inline("❌ Reject", f"otreject:{pending_id}".encode()),
            ],
        ]
        await client.send_message(
            APPROVAL_CHAT_ID,
            f"✏️ Edited draft for `{pending_id}`:\n\n{new_text}",
            buttons=buttons,
            parse_mode="md",
        )
