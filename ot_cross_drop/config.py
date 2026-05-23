"""Module config — loaded from coineasy-forwarder's existing .env.

Add these keys to forwarder's existing .env file:
    OT_SOURCE_CHANNEL=@Origintrailkr
    OT_TARGET_CHANNELS=@OriginTrail,@OriginTrailClub
    OT_APPROVAL_CHAT_ID=<int>
    OT_ADMIN_USER_IDS=<comma-separated ints>
    OT_AUTO_APPROVE=false
    OT_SEND_DELAY_SECONDS=2
"""
import os

# All OT_* prefixed to avoid clashing with forwarder's existing env vars.
SOURCE_CHANNEL = os.getenv("OT_SOURCE_CHANNEL", "@Origintrailkr")
TARGET_CHANNELS = [
    ch.strip() for ch in os.getenv(
        "OT_TARGET_CHANNELS",
        "@OriginTrail,@OriginTrailClub",
    ).split(",")
    if ch.strip()
]

APPROVAL_CHAT_ID = int(os.environ["OT_APPROVAL_CHAT_ID"].strip())
ADMIN_USER_IDS = [
    int(x) for x in os.getenv("OT_ADMIN_USER_IDS", "").split(",") if x.strip()
]

# Metric capture intervals (minutes)
METRIC_INTERVALS = [60, 360, 1440]  # 1h, 6h, 24h

# Reuse forwarder's existing Supabase connection if it has one.
# Otherwise set these:
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

AUTO_APPROVE = os.getenv("OT_AUTO_APPROVE", "false").lower() == "true"
SEND_DELAY_SECONDS = int(os.getenv("OT_SEND_DELAY_SECONDS", "2"))
