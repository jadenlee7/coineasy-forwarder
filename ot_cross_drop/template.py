"""Render EN drop messages with rotating variants to avoid spam pattern."""
import random

# Variants rotate to keep the global channel from feeling templated.
# Tone: warm, peer-to-peer, low friction. Single CTA.
VARIANTS = [
    (
        "Fresh post from Korean OriginTrail community 🇰🇷❤️\n"
        "Help us grow our base by sharing, liking and bookmarking 👇\n\n"
        "{link}"
    ),
    (
        "KR community just dropped a new piece 🇰🇷\n"
        "A share / like / bookmark goes a long way 🙏\n\n"
        "{link}"
    ),
    (
        "New from OriginTrail Korea 🇰🇷❤️\n"
        "Boost us with a quick share, like or bookmark 👇\n\n"
        "{link}"
    ),
    (
        "Korea community update 🇰🇷\n"
        "If you've got 10 seconds — share, like, or bookmark 🙏\n\n"
        "{link}"
    ),
]


def render(link: str, variant: int | None = None) -> str:
    """Render a drop message. Pass `variant` index for deterministic output."""
    template = VARIANTS[variant] if variant is not None else random.choice(VARIANTS)
    return template.format(link=link)
