# coineasy-forwarder — Agent Knowledge Base

> Operational knowledge for AI agents working on this codebase.
> Last updated: 2026-05-23 (PR #4 fix + OT cross-drop E2E validation).

---

## Telethon userbot pitfalls

### events.NewMessage(chats=CHAT_ID) — DO NOT USE for super-groups

Passing a negative super-group ID (-100...) to the chats= filter causes
Telethon to trigger entity resolution at handler registration time. This
blocks the entire event dispatch pipeline until the resolve completes.

Symptoms:
- Forwarder goes silent (no incoming/outgoing message handling)
- Railway logs show Connecting to ... appearing twice instead of once
- All handlers (main forwarder + ot_cross_drop) stop firing simultaneously

Correct pattern:

    # BAD
    @client.on(events.NewMessage(chats=APPROVAL_CHAT_ID))
    async def handler(event): ...

    # GOOD
    @client.on(events.NewMessage())
    async def handler(event):
        if event.chat_id != APPROVAL_CHAT_ID:
            return
        ...

Reference: PR #3 regression -> PR #4 fix (approval.py, 2026-05-23)

---

## Timezone debugging pitfall (2026-05-23)

System timezone alignment (do not change):
- Supabase DB: UTC (now() returns UTC, timestamptz columns)
- Railway containers: UTC
- Operator (Jaden): Dubai (GMT+4) or Seoul (KST/UTC+9) depending on travel

When timestamps "don't match":
1. Check your current timezone offset first
2. Telegram shows timestamps in your device's local timezone
3. Convert: DB UTC + your offset = what you see on screen
4. If they match, the system is correct

Worked example (2026-05-23):
- Bot response showed "10:15 AM" on screen
- DB sent_at: 06:15:43 UTC
- Operator was in Dubai (GMT+4): 06:15 + 4 = 10:15 = match
- No bug. Almost filed a timezone fix ticket.

---

## OT cross-drop — validated end-to-end flow (2026-05-23)

@Origintrailkr -> @OriginTrail + @OriginTrailClub cross-posting system.

### Flow
1. KR post published in @Origintrailkr
2. Main forwarder -> @coiniseasy (independent, no interference)
3. ot_cross_drop.monitor -> preview sent to CoinEasy Management group
4. Operator sends /otapprove or /otreject or /otedit
5. Bot responds with 2-step confirmation
6. Row inserted into Supabase ot_cross_drops table

### Supabase schema
- ot_cross_drops: id, kr_msg_id, drop_link, drop_msg, sent_at, targets (jsonb), created_at
  - No status column. sent_at presence = sent.
  - targets: [{"msg_id": 678868, "channel": "@OriginTrail"}, ...]
- ot_cross_drop_metrics: id, kr_msg_id, interval_minutes, snapshot (jsonb), captured_at, created_at
  - Separate scheduler captures views/reactions at T+30min etc.

### Verified test case
- kr_msg_id=235, @OriginTrail msg_id=678868, @OriginTrailClub msg_id=209123

---

## Railway debugging signals

| Signal | Meaning |
|---|---|
| Connecting to... 1x | Normal |
| Connecting to... 2x+ | Dispatch hold (see Telethon pitfall) |
| No Connection complete! | Auth failure or corrupt session |
| Both forwarder + ot_cross_drop silent | Shared client dead |
| Only one module silent | Module-specific handler bug |
| DB timestamps off | Check your timezone first (see Timezone pitfall) |
