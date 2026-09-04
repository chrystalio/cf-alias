# 🌩️ cf-alias

Command-line Cloudflare email aliases. Because your primary inbox deserves peace, quiet, and zero unwanted newsletters.

A lightweight Python CLI tool to generate and manage Cloudflare Email Routing aliases on the fly, directly from your terminal.

## Features

- **Quick create:** Generate a new email alias in seconds — no dashboard required.
- **Idempotent:** Running `cf-alias create github` twice won't duplicate the rule — you'll get a warning instead.
- **Spam prevention:** Ditch the catch-all. Use explicit aliases to block spam at the network edge.
- **Simple config:** Securely store your Cloudflare credentials and default forwarding address locally.
- **Install once, run anywhere:** Ships as a Python package with a `cf-alias` console-script entry point — no `python …` prefix needed after install.

## Prerequisites

Before you begin, you will need:

1. A domain with Cloudflare Email Routing enabled.
2. A Cloudflare API Token with **Email Routing: Edit** permissions.
3. Your domain's **Zone ID** (found on the right-hand sidebar of your Cloudflare dashboard overview).
4. Python 3.10+ (matches `pyproject.toml` `requires-python`).

## Installation

### Option A — Install as a package (recommended)

This installs `cf-alias` as a command on your `PATH` so you can run it from anywhere.

**With `uv` (recommended):**

```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
uv tool install .
```

`uv tool install` drops `cf-alias` into its own isolated environment and exposes the command on your `PATH` — no venv activation needed. Update it with `uv tool install --reinstall .` and remove it with `uv tool uninstall cf-alias`.

> **Pulling new code? Run `uv cache clean cf-alias && uv tool install --reinstall .`.** `uv tool install --reinstall` rebuilds from the working tree, but if the cached wheel from your previous install is newer than your source file's mtime (common after `git pull`), it'll still serve the stale build. Clearing the cache forces a fresh build.

**With `pip` (editable install in a venv):**

```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -e .
```

After any of the above, run `cf-alias --help` to confirm the install worked.

### Option B — Run the script directly (no package install)

If you'd rather skip the install and just run the file:

**With `uv` (simplest — no venv needed):**

```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
uv run python cf_alias.py --help
```

`uv run` resolves the deps from `pyproject.toml` into a throwaway env each time.

**With `pip` + venv (deps only, no package install):**

```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install cloudflare python-dotenv
```

Then run `python cf_alias.py …` for every command. The file is `cf_alias.py`, not `cf-alias.py` — hyphens aren't valid in Python module names.

### Why is the CLI called `cf-alias` but the file `cf_alias.py`?

The `[project.scripts]` entry in `pyproject.toml` is what installs the `cf-alias` binary on your `PATH`. The Python module name uses an underscore because Python doesn't allow hyphens in identifiers.

## Configuration

`cf-alias` looks for your `.env` file in this order:

1. The path in `CF_ALIAS_ENV` (if set) — e.g. `CF_ALIAS_ENV=/path/to/.env`.
2. `~/.config/cf-alias/.env` on Linux/macOS, or `%APPDATA%\cf-alias\.env` on Windows.
3. A `.env` next to the script (dev / `python cf_alias.py`).

If you run `cf-alias` and none of these exist, the script prints the exact path it expected and a template to fill in. To set things up from scratch:

```bash
mkdir -p ~/.config/cf-alias
cp .env.example ~/.config/cf-alias/.env  # .env.example is included in the repo
```

Then open the file and replace the placeholder values with your actual Cloudflare credentials:

```env
CF_API_TOKEN=your_actual_api_token_here
CF_ZONE_ID=your_actual_zone_id_here
DEFAULT_FORWARD_TO=email@example.com
DOMAIN=your_domain_here
```

The `.env` files are never committed to the repo.

If `cf-alias` prints a "Missing required environment variables" message, it means one or more of the four above is unset or empty. The same template is embedded in the script output — paste it into the path it tells you.

## Troubleshooting

**`cf-alias` is crashing on a bug you already fixed in the source.**

The tool binary lives in its own uv environment (`~/.local/share/uv/tools/cf-alias/`), separate from your working tree. A normal reinstall will serve a cached build from before your fix landed. Force a fresh build:

```bash
uv cache clean cf-alias && uv tool install --reinstall .
```

If you still see the bug, confirm the installed file actually has your fix:

```bash
grep -c "_safe_cell" ~/.local/share/uv/tools/cf-alias/lib/python3.12/site-packages/cf_alias.py
```

A non-zero count means the new code is installed; `0` means the reinstall didn't pick up your source.

## Usage

> The examples below use the installed `cf-alias` command. If you're running the script directly, swap `cf-alias` for `python cf_alias.py` (e.g. `python cf_alias.py create github`). Run `cf-alias --help` any time for the full command list.

**Create a new alias:**

Creates a new alias rule — `github@yourdomain.com` — forwarding to your default destination address. If the alias already exists, `cf-alias` prints a warning and exits without creating a duplicate.

```bash
cf-alias create github
```

**List all aliases:**

Print every routing rule on the zone as an aligned table — alias, destination, rule ID, and status in columns. Empty zones print a "No email routing rules found" notice. Example:

```
📜 Email Routing Rules 📜

ALIAS         FORWARD TO    RULE ID    STATUS
──────────    ────────────  ─────────  ───────
github@…      me@gmail.com  abc12345   Active
aws@…         me@gmail.com  def67890   Active
```

```bash
cf-alias list
```

**Delete an alias:**

Pass the `Rule ID` from the `list` output to remove the rule. By default, `delete` prompts `Are you sure you want to delete rule <rule_id>? [y/N]` before touching the API — answer `y` or `Y` to proceed, anything else aborts without changes.

```bash
cf-alias delete <rule_id>
```

Skip the prompt with `-y` / `--yes` for scripted or non-interactive use:

```bash
cf-alias delete <rule_id> --yes
```

Preview what would happen without actually calling the API using `--dry-run`:

```bash
cf-alias delete <rule_id> --dry-run
```

**Interactive menu:**

Launch the interactive arrow-key menu to create, list, delete, and categorize aliases. Each option prompts you for input and confirms destructive actions before applying them.

```bash
cf-alias tui
```

Navigation: use the arrow keys to move between options, `Enter` to confirm, and `Ctrl+C` to cancel and return to the previous menu.
