# Generated Alias Name for `create` Command — Design

**Date:** 2026-09-04
**Status:** Draft

## Problem

`cf-alias create` requires the user to type a name. Many users just want a throwaway alias for a signup form and would rather have one generated. The existing CLI supports only a custom name; there's no path to a generated one without copy-pasting from an external source.

## Goal

Extend `cf-alias create` so the user can either:
- **Custom**: provide a `name` (existing behavior), or
- **Generated**: ask the CLI to pick a name with a flag.

## Non-Goals

- No change to the `name` positional argument's syntax or meaning.
- No change to `list`, `delete`, `categorize`, or `tui`.
- No migration of existing aliases.
- No plural names, hyphens, or separators (see Decision 2 below).

## Approach

Add two flags to `cf-alias create` and one new helper module.

### Decisions

1. **Trigger UX** — A `--generate` flag on `create`. `name` remains the existing positional but becomes optional. Both `cf-alias create github` and `cf-alias create --generate` work.
2. **Generation format** — A single random English word from the `faker` library (no hyphenation, no separators, no digits). The format is intentionally short to keep common typos at bay and look clean in a signup form: e.g. `sparrow`, `blueheron`, `cedar`.

   *Note: the brainstorming dialogue initially landed on `Word.word()` (a single faker noun). The chosen format is "single faker word," which is the simplest and yields the shortest, most memo-able alias.*

3. **New dependency** — Add `faker` to `pyproject.toml`'s `dependencies` list.
4. **Dry-run escape hatch** — `--print-only` prints the generated name and exits 0 before any Cloudflare API call. Pair it with `--generate` for visibility.
5. **Collision handling** — Generate, then ask Cloudflare whether `{word}@{domain}` already exists (the existing pagination loop already does this). Retry up to 10 times, then exit non-zero with a clear message.

## Architecture

```
cf_alias/
  __init__.py       # unchanged
  __main__.py       # unchanged
  main.py           # argparse: --generate, --print-only; create-loop retry branch
  generator.py      # NEW — single public function: generate_alias_name()
  db.py             # unchanged
  tui.py            # unchanged
tests/
  test_generator.py # NEW — pytest unit tests for the generator
```

## Module: `cf_alias/generator.py`

A thin wrapper around the `faker` library.

```python
"""Random alias name generator backed by faker."""
from __future__ import annotations

import faker

_FAKER = faker.Faker()


def generate_alias_name() -> str:
    """Return a single, lowercase, ASCII English word suitable for an alias.

    Examples: 'sparrow', 'blueheron', 'cedar'.

    Returns:
        A lowercase ASCII string (letters only, no digits, no separators).
    """
    ...
```

The body of `generate_alias_name()` picks a random word via `faker` and lowercases it. Pick the faker provider — candidate options:

- `faker.Faker().word()` — a single English word (already `str.strip()`-friendly, no spaces).
- `faker.Faker().words(nb=1)[0]` — equivalent with explicit nb.

Both yield a single English word from a large dictionary. Concrete provider choice is a detail for implementation; the spec locks the contract: `-> str`, a single word, ASCII lowercase, no digits, no separators.

## `main.py` changes

### Argparse

`create` parser:

```python
add_parser = subparsers.add_parser("create", help="Create a new email alias")
add_parser.add_argument(
    "name",
    type=str,
    nargs="?",
    default=None,
    help="Name of the email alias (required unless --generate)",
)
add_parser.add_argument(
    "--generate",
    action="store_true",
    help="Auto-generate a random alias name (used in place of NAME)",
)
add_parser.add_argument(
    "--print-only",
    action="store_true",
    help="With --generate: print the generated name and exit (no API call)",
)
add_parser.add_argument(
    "--category", type=str, default=None, help="Category tag for the alias"
)
```

The `name` positional becomes `nargs="?"` with `default=None`.

### Validation

Reject combinations the user can't make sense of:

- `name` AND `--generate` together: error and exit.
- Neither `name` nor `--generate`: error and exit.
- `--print-only` without `--generate`: error and exit.

### Generate-or-resolve logic

```python
from .generator import generate_alias_name

if args.generate and not args.print_only:
    # Retry loop — generate, check Cloudflare, repeat until unique or 10 tries.
    attempts = 0
    while attempts < 10:
        candidate = generate_alias_name()
        attempts += 1
        if not _alias_exists(ctx, f"{candidate}@{ctx.domain}"):
            args.name = candidate
            break
    else:
        raise SystemExit(
            "Could not generate a unique alias after 10 attempts. "
            "Try again or pass a custom name."
        )
elif args.generate and args.print_only:
    print(generate_alias_name())
    return
```

`_alias_exists(ctx, full_email)` is a small private helper extracted from the current duplicate-check loop in `create`. It returns `True` if `{full_email}` exists with the default forward destination (existing "already exists" branch) or with a different destination (we treat that as a collision too — it still isn't unique).

If `_alias_exists` returns `False` we proceed to the normal creation block with `args.name = candidate`. The rest of the `create` flow (success print, optional category save) runs unchanged.

If `name` was passed directly (no `--generate`), the existing logic runs untouched.

## Error Handling

| Failure | Behavior |
|---|---|
| `name` + `--generate` both given | Exit 2 with usage hint: "Pass only one of NAME or --generate." |
| Neither `name` nor `--generate` | Exit 2 with usage hint: "Provide a NAME or use --generate." |
| `--print-only` without `--generate` | Exit 2 with usage hint: "--print-only requires --generate." |
| 10 collisions in a row | Exit 1 with "Could not generate a unique alias after 10 attempts." |
| Faker import fails at runtime | Exit 1 with: "`faker` is not installed. Run: uv pip install faker" |
| Network/auth failure on Cloudflare call | Existing behavior — propagated from the SDK |

## Testing

Add `tests/test_generator.py` with pytest. Tests:

1. `test_returns_nonempty_string` — `generate_alias_name()` returns truthy `str`
2. `test_is_lowercase` — output matches `^[a-z]+$`
3. `test_has_no_separators` — no hyphens, underscores, spaces, or digits
4. `test_returns_different_values` — call 50 times, observe ≥10 unique values (sanity check the random)

Fixtures not required. Faker is the only runtime dep added beyond the existing `cloudflare`, `python-dotenv`, `questionary`, `rich`.

## Verification

Implementation is "complete" once:

1. `uv pip install -r requirements.txt` succeeds with the new `faker` dep.
2. `python -m cf_alias create --help` lists `--generate` and `--print-only`.
3. `python -m cf_alias create --generate --print-only` prints a single word and exits 0.
4. `python -m cf_alias create github` still works (no regression).
5. `pytest tests/test_generator.py` passes.
6. `ruff check cf_alias/ tests/` clean.
7. `pyright cf_alias/ tests/` clean.

## Migration / Compatibility

- Existing users of `cf-alias create <name>` see no change.
- The `name` positional becomes optional, but no existing invocation breaks — every prior call passed a name.
