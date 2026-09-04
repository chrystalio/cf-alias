<div align="center">

# ⚡ cf-alias

**Cloudflare email aliases from your terminal. Your primary inbox deserves peace, quiet, and zero unwanted newsletters.**

</div>

| License | Python | Install |
|---------|--------|---------|
| ![MIT](https://img.shields.io/badge/license-MIT-blue) | ![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue) | ![uv](https://img.shields.io/badge/uv-tool-orange) |

---

## Features

| Goal | One-liner |
|------|-----------|
| Create | `cf-alias create github` |
| Generate random | `cf-alias create --generate` |
| Tag at creation | `--category dev` |
| List | `cf-alias list` |
| Delete safely | `cf-alias delete <id>` (with confirm prompt) |
| Categorize | local SQLite tag attached to rule ID |
| TUI | arrow-key menu + rich tables |

Run `cf-alias <subcommand> --help` for the full flag list.

---

## Prerequisites

1. **A domain** with Cloudflare Email Routing enabled.
2. **A Cloudflare API token** with **Email Routing: Edit** permission.
3. **Your zone ID** — visible in the right sidebar of your Cloudflare dashboard.
4. **Python 3.10+** (or use [`uv`](https://github.com/astral-sh/uv), which can manage Python for you).

---

## Quick Start

```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
cp .env.example .env       # fill in your Cloudflare values
uv tool install .          # or: pip install -e .
cf-alias create github
```

---

## Installation

Pick whichever path matches your environment. They all do the same thing.

### `uv tool install .` (recommended)

Drops `cf-alias` on your `PATH`. No venv to manage.

```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
uv tool install .
```

**Update after a `git pull`** — clearing the cache avoids serving a stale wheel:

```bash
uv cache clean cf-alias && uv tool install --reinstall .
```

**Uninstall:** `uv tool uninstall cf-alias`.

### `pip install -e .` (in a venv)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

### `uv run` (no install, throws away the env each run)

```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
uv run python -m cf_alias --help
```

### Run the package manually (no `pip install`)

```bash
pip install cloudflare python-dotenv questionary rich faker
python -m cf_alias --help
```

> The CLI command is `cf-alias` but the Python module is `cf_alias` — Python doesn't allow hyphens in identifiers. `pyproject.toml`'s `[project.scripts]` exposes the hyphenated name.

---

## Configuration

`cf-alias` looks for your `.env` in this order:

1. `$CF_ALIAS_ENV` if set
2. `~/.config/cf-alias/.env` (Linux/macOS) or `%APPDATA%\cf-alias\.env` (Windows)
3. A `.env` next to the source (dev mode)

```bash
mkdir -p ~/.config/cf-alias
cp .env.example ~/.config/cf-alias/.env
```

Edit it:

```env
CF_API_TOKEN=your_actual_api_token_here
CF_ZONE_ID=your_actual_zone_id_here
DEFAULT_FORWARD_TO=email@example.com
DOMAIN=your_domain_here
```

`.env` is gitignored. If `cf-alias` reports a missing env var, it prints the path and a template you can paste.

---

## Usage

CLI form: `cf-alias <subcommand> [options]`.

### create — add a new alias

```bash
cf-alias create github
```

Creates `github@<DOMAIN>` forwarding to `DEFAULT_FORWARD_TO`. If the alias already exists, prints a warning and exits — no duplicates.

**Generate a random name** when you don't care what it's called:

```bash
cf-alias create --generate           # name is a random English word
cf-alias create --generate --print-only  # preview only, no API call
```

The generator retries up to 10 times on collision; after that, pass a custom name.

**Tag at creation time** with a category stored locally:

```bash
cf-alias create github --category dev
```

### list — show every routing rule

```bash
cf-alias list
```

Aligned table — alias, destination, rule ID, status, category. Categories are stored in `~/.config/cf-alias/categories.db` (SQLite), separate from the Cloudflare API.

### delete — remove an alias

```bash
cf-alias delete <rule_id>
```

By default, prompts `Are you sure? [y/N]` before touching the API. Flags:

```bash
cf-alias delete <rule_id> --yes      # skip prompt (scripted use)
cf-alias delete <rule_id> --dry-run  # show what would happen, no API call
```

### categorize — tag an existing rule

```bash
cf-alias categorize <rule_id> dev       # set category
cf-alias categorize <rule_id> --clear  # remove category
```

Tags live in your local SQLite file, independent of the Cloudflare API.

### tui — interactive menu

```bash
cf-alias tui
```

Arrow-key menu built on `questionary` + `rich`. Menu: Create · List · Delete · Categorize · Quit.

Navigation: arrow keys to move, `Enter` to confirm, `Ctrl+C` to cancel.

---

## Troubleshooting

**My local fix isn't reflected in the installed binary.**

The uv-tool binary lives at `~/.local/share/uv/tools/cf-alias/`, separate from your working tree. A normal reinstall can serve a stale cached wheel. Force a fresh build:

```bash
uv cache clean cf-alias && uv tool install --reinstall .
```

**`Missing required environment variables`**

One of `CF_API_TOKEN`, `CF_ZONE_ID`, `DEFAULT_FORWARD_TO`, `DOMAIN` is unset or empty. Paste the template from the [Configuration](#configuration) section into the path `cf-alias` printed.

**`Alias 'x@y.com' already exists`**

The rule already lives in your zone. Pick a different name, or delete it first via `cf-alias list` → `cf-alias delete <id>`.

**`Could not generate a unique alias after 10 attempts`**

The random-name generator tried 10 words and every one collided. Try again, or pass a custom name.

**`ImportError: No module named 'cf_alias'` (running tests)**

Install the package in editable mode: `uv pip install -e .` (or `pip install -e .` with venv active).

---

## License

MIT.
