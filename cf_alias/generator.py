"""Random alias name generator backed by faker."""

from __future__ import annotations

import faker

_FAKER = faker.Faker()


def generate_alias_name() -> str:
    """Return a lowercase ASCII English compound name suitable for an alias.

    Combines a random faker word with a random faker first name, both
    lowercased and concatenated with no separator.

    Examples: 'sparrowsmith', 'blueheronrachel', 'cedarjames'.

    Returns:
        A lowercase ASCII string containing only letters (a-z).
    """
    word = _FAKER.word()
    name = _FAKER.first_name()
    return f"{word}{name}".lower()
