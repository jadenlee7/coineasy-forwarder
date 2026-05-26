"""Render EN drop messages with rotating variants to avoid spam pattern."""
import random

# Each variant has two parts: a Telegram announcement opener (always shown)
# and an X-post CTA (only shown when an X link was found in the KR post).
# Tone: warm, peer-to-peer, low friction.
VARIANTS = [
    {
        "announce": "New announcement from OriginTrail Korea 🇰🇷❤️\n{tg_link}",
        "cta": "Boost the X post — share, like or bookmark 👇\n{x_link}",
    },
    {
        "announce": "Fresh update from the Korean OriginTrail community 🇰🇷\n{tg_link}",
        "cta": "A quick share / like / bookmark on X goes a long way 🙏\n{x_link}",
    },
    {
        "announce": "OriginTrail Korea just posted something new 🇰🇷❤️\n{tg_link}",
        "cta": "Help us grow — give the X post a share, like or bookmark 👇\n{x_link}",
    },
    {
        "announce": "Korea community update 🇰🇷\n{tg_link}",
        "cta": "If you've got 10 seconds — share, like, or bookmark the X post 🙏\n{x_link}",
    },
]


def render(tg_link: str, x_link: str | None = None, variant: int | None = None) -> str:
    """Render a drop message.

    Always includes the KR Telegram announcement link. When an X post link is
    available, appends an engagement CTA pointing at it. Pass `variant` index
    for deterministic output.
    """
    v = VARIANTS[variant] if variant is not None else random.choice(VARIANTS)
    parts = [v["announce"].format(tg_link=tg_link)]
    if x_link:
        parts.append(v["cta"].format(x_link=x_link))
    return "\n\n".join(parts)
