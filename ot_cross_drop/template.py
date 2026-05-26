"""Render EN drop messages with rotating variants to avoid spam pattern."""
import random

# Variants rotate to keep the global channel from feeling templated.
# Tone: warm, peer-to-peer, low friction. Points at the KR Telegram announcement.
VARIANTS = [
    "New announcement from OriginTrail Korea 🇰🇷❤️\nGive it a read & show some love 👇\n\n{tg_link}",
    "Fresh update from the Korean OriginTrail community 🇰🇷\nWorth a quick look 👇\n\n{tg_link}",
    "OriginTrail Korea just posted something new 🇰🇷❤️\nCheck it out 👇\n\n{tg_link}",
    "Korea community update 🇰🇷\nTake a look 👇\n\n{tg_link}",
]


def render(tg_link: str, variant: int | None = None) -> str:
    """Render a drop message pointing at the KR Telegram announcement.

    Pass `variant` index for deterministic output.
    """
    template = VARIANTS[variant] if variant is not None else random.choice(VARIANTS)
    return template.format(tg_link=tg_link)
