# 🌩️ cf-alias

Command-line Cloudflare email aliases. Because your primary inbox deserves peace, quiet, and zero unwanted newsletters.

A lightweight Python CLI tool to generate and manage Cloudflare Email Routing aliases on the fly, directly from your terminal.

---

## ✨ Features

* **Quick Create:** Generate a new email alias in seconds — no dashboard required.
* **Spam Prevention:** Ditch the catch-all. Use explicit aliases to block spam at the network edge.
* **Simple Config:** Securely store your Cloudflare credentials and default forwarding address locally.
* **Install once, run anywhere:** Ships as a Python package with a `cf-alias` console-script entry point — no `python …` prefix needed after install.

---

## 📋 Prerequisites

Before you begin, you will need:
1. A domain with Cloudflare Email Routing enabled.
2. A Cloudflare API Token with **Email Routing: Edit** permissions.
3. Your domain's **Zone ID** (found on the right-hand sidebar of your Cloudflare dashboard overview).
4. Python **3.10+** (matches `pyproject.toml` `requires-python`).

---

## 🚀 Installation

### Option A — Install as a package (recommended)

This installs `cf-alias` as a command on your `PATH` so you can run it from anywhere.

**With `uv` (recommended):**
```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
uv tool install .
```

`uv tool install` drops `cf-alias` into its own isolated environment and exposes the command on your `PATH` — no venv activation needed. Update it with `uv tool install --force .` and remove it with `uv tool uninstall cf-alias`.

**With `pip` (editable install in a venv):**
```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -e .
```

After any of the above, run `cf-alias --help` to confirm the install worked.

### Option B — Run the script directly (no install)

If you just want to poke at it without installing:

```bash
git clone https://github.com/chrystalio/cf-alias.git
cd cf-alias
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install .
```

Then run `python cf_alias.py …` for every command. (The file is `cf_alias.py`, not `cf-alias.py` — hyphens aren't valid in Python module names.)

### A note on `pyproject.toml`

Dependencies and the `cf-alias` console-script entry point are declared in `pyproject.toml`:

```toml
[project]
name = "cf-alias"
version = "0.1.0"
description = "Cloudflare Email Forwarding Alias Manager"
requires-python = ">=3.10"
dependencies = [
    "cloudflare",
    "python-dotenv",
]

[project.scripts]
cf-alias = "cf_alias:main"
```

The `[project.scripts]` entry is what installs the `cf-alias` binary — it points at `main` inside `cf_alias.py`. The hyphen in the CLI name comes from `pyproject.toml`; the module name uses an underscore because Python doesn't allow hyphens in identifiers.

---

## ⚙️ Configuration

`cf-alias` looks for your `.env` file in this order:

1. The path in `CF_ALIAS_ENV` (if set) — e.g. `CF_ALIAS_ENV=/path/to/.env`.
2. `~/.config/cf-alias/.env` on Linux/macOS, or `%APPDATA%\cf-alias\.env` on Windows.
3. A `.env` next to the script (dev / `python cf_alias.py`).

If you run an installed `cf-alias` and none of these exist, it prints the exact path and a template to fill in — just create the file there:

```bash
mkdir -p ~/.config/cf-alias
cp .env.example ~/.config/cf-alias/.env
```

Then open the file and replace the placeholder values with your actual Cloudflare credentials:

```env
CF_API_TOKEN=your_actual_api_token_here
CF_ZONE_ID=your_actual_zone_id_here
DEFAULT_FORWARD_TO=email@example.com
DOMAIN=your_domain_here
```

The `.env` files are never committed to the repo.

---

## 💻 Usage

> The examples below use the installed `cf-alias` command. If you're running the script directly, swap `cf-alias` for `python cf_alias.py` (e.g. `python cf_alias.py create github`).

**Create a new alias:**
Creates a new alias rule — `github@yourdomain.com` — forwarding to your default destination address.

```bash
cf-alias create github
```

**List all aliases:**
Print every routing rule on the zone, with the alias address, destination, rule ID, and status.

```bash
cf-alias list
```

**Delete an alias:**
Pass the `Rule ID` from the `list` output to remove the rule.

```bash
cf-alias delete <rule_id>
```

### View help

View all available commands and options.

```bash
cf-alias --help
```
