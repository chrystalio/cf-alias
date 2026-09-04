"""Unit tests for cf_alias.generator."""

import re

from cf_alias.generator import generate_alias_name


def test_returns_string():
    """generate_alias_name returns a string."""
    name = generate_alias_name()
    assert isinstance(name, str)


def test_returns_nonempty():
    """generate_alias_name returns a non-empty string."""
    name = generate_alias_name()
    assert name != ""
    assert name is not None


def test_is_lowercase_letters_only():
    """Generated name contains only lowercase ASCII letters."""
    name = generate_alias_name()
    assert re.fullmatch(r"[a-z]+", name), f"unexpected chars in {name!r}"


def test_has_no_separators():
    """Generated name contains no hyphens, underscores, spaces, or digits."""
    name = generate_alias_name()
    for ch in ("-", "_", " ", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
        assert ch not in name, f"unexpected separator/digit {ch!r} in {name!r}"


def test_returns_varied_values():
    """Generator produces variety across many calls."""
    names = {generate_alias_name() for _ in range(50)}
    assert len(names) >= 10, f"only saw {len(names)} unique names in 50 calls"
