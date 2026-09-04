"""Random alias name generator backed by faker."""

from __future__ import annotations

import faker

_FAKER = faker.Faker()


def generate_alias_name() -> str:
    """Return a single, lowercase, ASCII English word suitable for an alias.

    Examples: 'sparrow', 'blueheron', 'cedar'.

    Returns:
        A lowercase ASCII string containing only letters (a-z).
    """
    raw = _FAKER.word()
    return raw.lower()
