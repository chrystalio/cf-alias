"""Unit tests for cf_alias.generator."""

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
