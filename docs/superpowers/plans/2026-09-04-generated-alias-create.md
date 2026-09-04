# Generated Alias Names for `create` Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `cf-alias create` either accept a custom `name` (existing behavior) or auto-generate one via a `--generate` flag, with an optional `--print-only` dry-run.

**Architecture:** New `cf_alias/generator.py` wraps `faker.Word.word()`. `main.py`'s argparse is extended with two flags; the existing duplicate-check pagination loop is reused for collision detection with a 10-attempt retry.

**Tech Stack:** Python 3.10+, `argparse`, `faker` (new dependency), `pytest`, `ruff`, `pyright`.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `pyproject.toml` | modify | Add `faker` to `dependencies` |
| `cf_alias/generator.py` | create | Single public function `generate_alias_name()` |
| `cf_alias/main.py` | modify | argparse: add `--generate`, `--print-only`; `create` branch: validation + generate-or-resolve + retry loop |
| `tests/test_generator.py` | create | pytest unit tests for `generate_alias_name()` |
| `requirements.txt` | update via uv lock | Reflects new faker dependency |

---

## Task 1: Add `faker` dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `faker` to the dependencies list**

Edit `pyproject.toml` so the `dependencies` block reads:

```toml
dependencies = [
    "cloudflare",
    "python-dotenv",
    "faker",
    "questionary>=2.0",
    "rich",
]
```

- [ ] **Step 2: Sync the venv**

Run:
```bash
source .venv/bin/activate && uv pip install -e .
```
Expected: install completes with no errors. The output mentions `faker` (or `Faker`) being installed/updated.

- [ ] **Step 3: Verify `faker` is importable**

Run:
```bash
source .venv/bin/activate && python -c "import faker; print(faker.Faker().word())"
```
Expected: prints a single English word (e.g. `science`, `beauty`).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat(deps): add faker for alias name generation"
```

---

## Task 2: First failing generator test

**Files:**
- Create: `tests/test_generator.py`

- [ ] **Step 1: Create the tests directory if absent**

Run:
```bash
mkdir -p tests
```
This is a no-op if the directory exists.

- [ ] **Step 2: Write the failing test**

Create `tests/test_generator.py`:

```python
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
```

- [ ] **Step 3: Run the test to verify it fails**

Run:
```bash
source .venv/bin/activate && pytest tests/test_generator.py -v
```
Expected: `ImportError: cannot import name 'generate_alias_name' from 'cf_alias.generator'`. Both tests fail.

- [ ] **Step 4: Commit the failing test**

```bash
git add tests/test_generator.py
git commit -m "test(generator): add initial failing tests for alias generation"
```

---

## Task 3: Minimal generator implementation

**Files:**
- Create: `cf_alias/generator.py`

- [ ] **Step 1: Create `generator.py` with the implementation**

```python
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
```

- [ ] **Step 2: Run the test to verify it passes**

Run:
```bash
source .venv/bin/activate && pytest tests/test_generator.py -v
```
Expected: 2 passed.

- [ ] **Step 3: Smoke-check the generator directly**

Run:
```bash
source .venv/bin/activate && python -c "from cf_alias.generator import generate_alias_name; print(generate_alias_name())"
```
Expected: a single lowercase English word, no spaces or punctuation.

- [ ] **Step 4: Commit**

```bash
git add cf_alias/generator.py
git commit -m "feat(generator): add faker-backed alias name generator"
```

---

## Task 4: Add format and randomness tests

**Files:**
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Add the new test functions**

Append to `tests/test_generator.py`:

```python
import re


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
```

- [ ] **Step 2: Run the test suite**

Run:
```bash
source .venv/bin/activate && pytest tests/test_generator.py -v
```
Expected: 5 passed (the 2 from Task 2 + these 3 new ones).

- [ ] **Step 3: Commit**

```bash
git add tests/test_generator.py
git commit -m "test(generator): cover format and randomness of generated names"
```

---

## Task 5: Add argparse flags to `create`

**Files:**
- Modify: `cf_alias/main.py:151-160`

- [ ] **Step 1: Make `name` optional and add `--generate` and `--print-only` flags**

In `cf_alias/main.py`, locate the current `add_parser` block (around lines 156-160):

```python
add_parser = subparsers.add_parser("create", help="Create a new email alias")
add_parser.add_argument("name", type=str, help="Name of the email alias to add")
add_parser.add_argument(
    "--category", type=str, default=None, help="Category tag for the alias"
)
```

Replace it with:

```python
add_parser = subparsers.add_parser("create", help="Create a new email alias")
add_parser.add_argument(
    "name",
    type=str,
    nargs="?",
    default=None,
    help="Name of the email alias (omit with --generate)",
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

- [ ] **Step 2: Verify argparse renders the new flags**

Run:
```bash
source .venv/bin/activate && python -m cf_alias create --help
```
Expected: output shows `name` as optional (in brackets), lists `--generate`, and lists `--print-only`.

- [ ] **Step 3: Commit**

```bash
git add cf_alias/main.py
git commit -m "feat(cli): add --generate and --print-only flags to create command"
```

---

## Task 6: Add flag combination validation

**Files:**
- Modify: `cf_alias/main.py:191-198`

- [ ] **Step 1: Locate the validation hook point**

In `cf_alias/main.py`, the current flow right after `args = parser.parse_args()` is:

```python
args = parser.parse_args()

if not args.command:
    parser.print_help()
    return
```

Add the validation block immediately after `if not args.command:` block (i.e., between `return` of the no-command branch and `ctx = build_context()`).

- [ ] **Step 2: Insert the validation logic**

Add this block right after the `if not args.command:` block:

```python
    if args.command == "create":
        if args.name and args.generate:
            raise SystemExit(
                "Pass only one of NAME or --generate."
            )
        if not args.name and not args.generate:
            raise SystemExit(
                "Provide a NAME or use --generate."
            )
        if args.print_only and not args.generate:
            raise SystemExit(
                "--print-only requires --generate."
            )
```

- [ ] **Step 3: Manually exercise the validation paths**

Run each command below. They should all print the expected usage error and exit non-zero:

```bash
source .venv/bin/activate && python -m cf_alias create github --generate
```
Expected: `Pass only one of NAME or --generate.`

```bash
source .venv/bin/activate && python -m cf_alias create
```
Expected: `Provide a NAME or use --generate.`

```bash
source .venv/bin/activate && python -m cf_alias create github --print-only
```
Expected: `--print-only requires --generate.`

(These will exit with non-zero status before any Cloudflare call since validation fires before `build_context()`.)

- [ ] **Step 4: Confirm a valid combination still parses**

Run:
```bash
source .venv/bin/activate && python -m cf_alias create --generate --help
```
Expected: prints the create subcommand help. (No validation errors.)

Run:
```bash
source .venv/bin/activate && python -m cf_alias create --help
```
Expected: shows create subcommand help, no errors.

- [ ] **Step 5: Commit**

```bash
git add cf_alias/main.py
git commit -m "feat(cli): validate flag combinations for create command"
```

---

## Task 7: Wire generator into the `create` flow

**Files:**
- Modify: `cf_alias/main.py` (`create` branch)

- [ ] **Step 1: Add the generator import**

In `cf_alias/main.py`, immediately after the `from . import db` import line (around line 14), add:

```python
from .generator import generate_alias_name
```

- [ ] **Step 2: Replace the create-branch body with the generate-or-resolve logic**

Locate the `if args.command == "create":` block (current lines around 199-257). Replace the entire block — from `target_email = f"{args.name}@{ctx.domain}"` down to (but not including) the `db.set_category(...)` call — with:

```python
    if args.command == "create":
        if args.print_only:
            # Validation guarantees --generate was passed.
            print(generate_alias_name())
            return

        if args.generate:
            attempts = 0
            while attempts < 10:
                candidate = generate_alias_name()
                attempts += 1
                # _alias_exists returns True if the alias exists at all
                # (regardless of where it forwards to).
                if not _alias_exists(ctx, f"{candidate}@{ctx.domain}"):
                    args.name = candidate
                    break
            else:
                raise SystemExit(
                    "Could not generate a unique alias after 10 attempts. "
                    "Try again or pass a custom name."
                )

        target_email = f"{args.name}@{ctx.domain}"
```

Preserve everything below this — the existing pagination loop, the `rules.create(...)` call, the success print, and the optional `db.set_category(...)` line stay exactly as they are.

- [ ] **Step 3: Add the `_alias_exists` helper**

Add the following helper function above `main()` in `cf_alias/main.py` (place it next to `_safe_cell` and `_rule_to_row`):

```python
def _alias_exists(ctx: AppContext, target_email: str) -> bool:
    """Return True if a rule with `target_email` exists in the zone, else False.

    Walks every page of `rules.list(...)` so a match on page 2+ is not missed.
    """
    page = ctx.client.email_routing.rules.list(zone_id=ctx.zone_id)
    while True:
        for rule in page:
            first_matcher = rule.matchers[0] if rule.matchers else None
            if first_matcher is not None and first_matcher.value == target_email:
                return True
        if page.has_next_page():
            page = page.get_next_page()
        else:
            return False
```

- [ ] **Step 4: Smoke-check `--print-only` (no Cloudflare call)**

Run:
```bash
source .venv/bin/activate && python -m cf_alias create --generate --print-only
```
Expected: prints a single lowercase English word and exits 0. **No** Cloudflare `.env` is required for this path because the `build_context()` step is short-circuited.

If `.env` is missing, this will still work — validation runs *before* `build_context()`.

- [ ] **Step 5: Confirm the existing custom-name path still parses**

Run:
```bash
source .venv/bin/activate && python -m cf_alias create github --help
```
Expected: argparse succeeds; help text prints.

- [ ] **Step 6: Lint**

Run:
```bash
source .venv/bin/activate && ruff check cf_alias/ tests/ && pyright cf_alias/ tests/
```
Expected: both commands exit 0 with no errors.

- [ ] **Step 7: Run the generator test suite**

Run:
```bash
source .venv/bin/activate && pytest tests/test_generator.py -v
```
Expected: 5 passed.

- [ ] **Step 8: Commit**

```bash
git add cf_alias/main.py
git commit -m "feat(create): wire generator into create flow with retry and dry-run"
```

---

## Self-Review Checklist (run after the plan is drafted)

- [x] **Spec coverage** — every spec requirement maps to a task:
  - `--generate` flag → Task 5
  - `--print-only` → Task 5 + Task 7
  - faker dep → Task 1
  - single-word generation → Task 3 + Task 4 format tests
  - collision retry loop → Task 7 (and `_alias_exists` extracted)
  - validation matrix → Task 6
  - unit tests → Tasks 2 + 4
  - verification block (ruff/pyright/pytest) → Task 7 Steps 6-7
- [x] **Placeholder scan** — no TBDs, no "implement later", complete code in every code step.
- [x] **Type consistency** — `generate_alias_name()` is referenced in Task 5/7 only after Task 3 defines it; `_alias_exists` is defined before being called in Task 7; `AppContext` already exists in the module.
