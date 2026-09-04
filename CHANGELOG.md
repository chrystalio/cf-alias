# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-09-04

### Added
- `create --generate` flags the CLI to pick a random alias name (word + first name via the `faker` library, e.g. `sparrowsmith`) instead of you supplying one. The generator walks every Cloudflare rule page and retries up to 10 times on collision, falling back to "use a custom name" if no unique name emerges.
- `create --generate --print-only` prints the generated name and exits without calling the Cloudflare API — useful for previewing a name before committing.
- `faker` added to `dependencies` in `pyproject.toml` (and reflected in `uv.lock`).
- `tui` create menu now offers a "Generate random name" option alongside the custom name prompt.

## [0.4.0] - 2026-09-04

### Added
- `delete` now prompts `Are you sure you want to delete rule <rule_id>? [y/N]` before calling the API; answering anything other than `y`/`Y` aborts without changes.
- `delete` accepts `-y` / `--yes` to skip the confirmation prompt for scripted/non-interactive use.
- `delete` accepts `--dry-run` to print which rule would be deleted and exit without touching the API.
- `create` accepts `--category <name>` to tag a new alias with a local category at creation time.
- `categorize` subcommand: `cf-alias categorize <rule_id> <category>` sets a category; `cf-alias categorize <rule_id> --clear` removes it. Categories are persisted in a local SQLite database at `~/.config/cf-alias/categories.db` (overridable via `CF_ALIAS_DB`), independent of the Cloudflare API.
- `tui` subcommand launches an interactive arrow-key menu for create, list, delete, and categorize. Shows a domain banner with watermark on launch, uses rich tables with `●`/`○` status icons for list rendering.
- `AppContext` dataclass and `build_context()` helper in `cf_alias.main` for sharing Cloudflare client + zone config between CLI and TUI.
- `cf_alias/db.py` module for local SQLite category storage with thread-safe `set_category`, `get_category`, `clear_category`, `list_by_category` helpers.
- Dev tooling: `ruff` (linting) and `pyright` (type checking) configured in `pyproject.toml`. Both run clean on the codebase.

### Fixed
- `list` and the create-branch idempotency check now paginate through **every** Cloudflare result page, not just the first one. Previously, a duplicate alias on page 2+ would slip through and create a duplicate rule.
- `create` idempotency now distinguishes between "alias exists with matching destination" (silent skip) and "alias exists with a different destination" (warning showing both addresses).
- `list` defensively coerces every table cell to a string before computing column widths or rendering, preventing `TypeError: object of type 'NoneType' has no len()` on rules with None-valued fields (e.g. worker/drop actions with no `value`).
- `delete` cleans up the matching SQLite category row after a successful API delete, so stale category entries don't accumulate.

### Changed
- Module-level dotenv loading is now lazy: `_load_env()` runs from `main()` instead of at import, so `import cf_alias.main` no longer has side effects.
- Argparse parsing happens before env validation, so `cf-alias --help` works without a populated `.env`.
- Cloudflare client construction moved into `build_context()` and runs after env validation, so missing tokens produce a clear "Missing required environment variables" message instead of an opaque SDK traceback.
- `list` output table now includes a `CATEGORY` column showing the locally-stored category (or blank when unset).
- TUI library: built initially with `textual`, then replaced with `questionary` (arrow-key menus) per feedback that the DataTable view was overkill. `textual` removed from `dependencies`; `questionary` and `rich` added.


## [0.3.0] - 2026-08-09

### Changed
- `create` is now idempotent: lists existing rules first and short-circuits with a warning if `{name}@{DOMAIN}` already exists, instead of creating a duplicate rule.
- `target_email` extracted to a local in the `create` branch and reused in the matcher, the duplicate check, and the success print (previously recomputed inline three times).

## [0.2.0] - 2026-08-08

### Changed
- Module renamed `cf-alias.py` → `cf_alias.py` (hyphens are illegal in Python module names).
- Project is now packaged as a Python package via PEP 621 `pyproject.toml`. The `cf-alias` console-script entry point exposes the CLI as a standalone command after install.
- Dependencies now live in `pyproject.toml`; `requirements.txt` has been removed.
- `requires-python = ">=3.10"`.

### Added
- `pyproject.toml` with `[project]` metadata, dependencies, and `[project.scripts]` entry point `cf-alias = "cf_alias:main"`.
- `uv.lock` for reproducible installs.
- `CLAUDE.md` project guidance.
- `CHANGELOG.md`.

### Documentation
- README rewritten to document the new install paths (`uv tool install .`, editable `pip install -e .`, script mode) and the `cf-alias` console-script entry point.

## [0.1.0] - 2026-08-08

Initial release. Single-file CLI for managing Cloudflare Email Routing aliases.

### Added
- Project scaffold: `.env.example`, `.gitignore`, `requirements.txt`, `README.md`.
- CLI skeleton with `argparse` subcommand dispatch and `dotenv`-based config loading.
- `create` subcommand: builds a literal `to` matcher and a `forward` action against `DEFAULT_FORWARD_TO` using the Cloudflare Python SDK.
- `list` subcommand: prints every routing rule on the zone with alias, destination, rule ID, and status.
- `delete` subcommand: removes a routing rule by ID.
- Top-level `--help` fallback when no subcommand is given.
- README documents the `create` / `list` / `delete` subcommands.

### Changed
- Imports rearranged to PEP 8 grouping.
- README placeholder repo URL replaced with the actual `chrystalio/cf-alias` repo.

### Removed
- Unused `requests` dependency dropped from `requirements.txt`.
