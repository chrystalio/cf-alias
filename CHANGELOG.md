# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `delete` now prompts `Are you sure you want to delete rule <rule_id>? [y/N]` before calling the API; answering anything other than `y`/`Y` aborts without changes.
- `delete` accepts `-y` / `--yes` to skip the confirmation prompt for scripted/non-interactive use.
- `delete` accepts `--dry-run` to print which rule would be deleted and exit without touching the API.
- `tui` subcommand to launch an interactive Textual UI for browsing, filtering, sorting, and editing aliases ([#PR])

## [0.3.1] - 2026-08-09

### Fixed
- `list` now defensively coerces every table cell to a string before computing column widths or rendering, preventing `TypeError: object of type 'NoneType' has no len()` on rules with None-valued fields (e.g. worker/drop actions with no `value`).

### Changed
- `list` output reformatted as a one-row-per-rule ASCII table with aligned columns (header + separator + rows), replacing the previous 5-line-per-rule block format. Empty rule list now prints a friendly "No email routing rules found" message instead of an empty table.

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
