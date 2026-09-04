import argparse
import os
import sys
from pathlib import Path

import dotenv
from cloudflare import Cloudflare

# Template for the user config file. No secrets — placeholders only.
ENV_TEMPLATE = """\
# ~/.config/cf-alias/.env (Linux/macOS)
# %APPDATA%\\cf-alias\\.env (Windows)
# Override with CF_ALIAS_ENV=/path/to/.env
CF_API_TOKEN=your_actual_api_token_here
CF_ZONE_ID=your_actual_zone_id_here
DEFAULT_FORWARD_TO=email@example.com
DOMAIN=your_domain_here
"""


def _config_path() -> Path:
    """Cross-platform location for the user's .env file.

    Priority: $CF_ALIAS_ENV if set → ~/.config/cf-alias/.env (Linux/macOS XDG)
    → ~/AppData/Roaming/cf-alias/.env (Windows).
    """
    override = os.environ.get("CF_ALIAS_ENV")
    if override:
        return Path(override)

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "cf-alias" / ".env"
    return Path.home() / ".config" / "cf-alias" / ".env"


def _find_env() -> Path | None:
    """Return the first .env path that exists, preferring the user config dir."""
    candidates = [
        _config_path(),
        Path(__file__).resolve().parent / ".env",  # dev: alongside the script
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


REQUIRED_ENV_VARS = ("CF_API_TOKEN", "CF_ZONE_ID", "DOMAIN", "DEFAULT_FORWARD_TO")

# Module-level constants populated lazily by _load_env().
CF_API_TOKEN: str | None = None
CF_ZONE_ID: str | None = None
DOMAIN: str | None = None
DEFAULT_FORWARD_TO: str | None = None


def require_env():
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise SystemExit(
            "Missing required environment variables: "
            + ", ".join(missing)
            + f"\nCreate a .env at: {_config_path()}"
            + "\n\nPaste this template and fill in your values:\n"
            + ENV_TEMPLATE
        )


def _require_env_str(name: str) -> str:
    """Return a non-None env var after require_env() has validated presence."""
    value = os.getenv(name)
    if value is None:
        raise SystemExit(f"Unexpectedly missing env var: {name}")
    return value


def _load_env():
    """Load .env file lazily and populate module constants.

    Called from main() so importing this module has no side effects.
    """
    global CF_API_TOKEN, CF_ZONE_ID, DOMAIN, DEFAULT_FORWARD_TO
    dotenv.load_dotenv(_find_env())
    CF_API_TOKEN = os.getenv("CF_API_TOKEN")
    CF_ZONE_ID = os.getenv("CF_ZONE_ID")
    DOMAIN = os.getenv("DOMAIN")
    DEFAULT_FORWARD_TO = os.getenv("DEFAULT_FORWARD_TO")


def main():
    _load_env()
    require_env()
    zone_id = _require_env_str("CF_ZONE_ID")
    domain = _require_env_str("DOMAIN")
    default_forward_to = _require_env_str("DEFAULT_FORWARD_TO")
    client = Cloudflare(api_token=CF_API_TOKEN)
    parser = argparse.ArgumentParser(
        description="Cloudflare Email Forwarding Alias Manager"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    add_parser = subparsers.add_parser("create", help="Create a new email alias")
    add_parser.add_argument("name", type=str, help="Name of the email alias to add")

    subparsers.add_parser("list", help="list of email aliases")

    delete_parser = subparsers.add_parser(
        "delete", help="Delete an existing email alias"
    )
    delete_parser.add_argument(
        "rule_id", type=str, help="ID of the email alias to delete"
    )
    delete_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation prompt"
    )
    delete_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "create":
        target_email = f"{args.name}@{domain}"

        # Paginate through ALL existing rules. Cloudflare's rules.list()
        # returns a SyncV4PagePaginationArray — iterate every page so we
        # don't miss a match sitting on page 2+.
        page = client.email_routing.rules.list(zone_id=zone_id)
        while True:
            for rule in page:
                existing_alias = rule.matchers[0].value if rule.matchers else None
                if existing_alias == target_email:
                    first_action = rule.actions[0] if rule.actions else None
                    existing_destination = None
                    if first_action is not None:
                        action_value = first_action.value
                        existing_destination = action_value[0] if action_value else None
                    if existing_destination == default_forward_to:
                        print(
                            f"\n⚠️  Alias '{target_email}' already exists and "
                            f"forwards to '{default_forward_to}'.\n"
                        )
                    else:
                        print(
                            f"\n⚠️  Alias '{target_email}' already exists but "
                            f"forwards to '{existing_destination}', not "
                            f"'{default_forward_to}'.\n"
                        )
                    return
            if page.has_next_page():
                page = page.get_next_page()
            else:
                break

        rule = client.email_routing.rules.create(
            zone_id=zone_id,
            name=f"Alias for {args.name}",
            enabled=True,
            matchers=[
                {
                    "type": "literal",
                    "field": "to",
                    "value": target_email,
                }
            ],
            actions=[
                {
                    "type": "forward",
                    "value": [default_forward_to],
                }
            ],
        )
        print("\n✨ Email Routing Rule Created Successfully! ✨")
        print(f"  • Alias       : {target_email}")
        print(f"  • Forward To  : {default_forward_to}")
        print(f"  • Rule ID     : {rule.id if rule else 'N/A'}")
        print("  • Status      : Active\n")

    elif args.command == "list":
        # Materialise every page so the table shows the full zone state.
        page = client.email_routing.rules.list(zone_id=zone_id)
        rules = list(page)
        while page.has_next_page():
            page = page.get_next_page()
            rules.extend(page)

        if not rules:
            print("\n📜 No email routing rules found for this zone.\n")
            return

        def _cell(value, missing="Unknown"):
            """Coerce a rule field into a printable string.
            Any None / missing → 'Unknown'.
            """
            if value is None:
                return missing
            return str(value) if value != "" else missing

        rows = []
        for rule in rules:
            try:
                first_matcher = rule.matchers[0] if rule.matchers else None
                alias_email = (
                    _cell(first_matcher.value, "N/A")
                    if first_matcher is not None
                    else "N/A"
                )
                first_action = rule.actions[0] if rule.actions else None
                if first_action is not None and first_action.value:
                    destination_email = _cell(first_action.value[0], "N/A")
                else:
                    destination_email = "N/A"
                rule_id = _cell(rule.id)
            except (IndexError, AttributeError, TypeError):
                alias_email = "Unknown"
                destination_email = "Unknown"
                rule_id = "Unknown"
            status = "Active" if rule.enabled else "Inactive"
            rows.append((alias_email, destination_email, rule_id, status))

        headers = ("ALIAS", "FORWARD TO", "RULE ID", "STATUS")

        # Defense in depth: coerce every cell to a string before measuring or
        # rendering. _cell() should have already done this, but if a future
        # SDK field shape leaks a None/non-str through, the table still renders
        # instead of raising TypeError on len()/ljust().
        def _safe_cell(value, missing="Unknown"):
            if value is None:
                return missing
            if isinstance(value, str):
                return value
            return str(value) if value != "" else missing

        safe_rows = [
            tuple(_safe_cell(c) for c in row)
            for row in rows
        ]
        safe_headers = tuple(_safe_cell(h, missing=h) for h in headers)

        widths = [
            max(len(safe_headers[i]), *(len(row[i]) for row in safe_rows))
            for i in range(len(safe_headers))
        ]

        def _fmt(cells):
            return "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(cells))

        print("\n📜 Email Routing Rules 📜\n")
        print(_fmt(safe_headers))
        print("  ".join("─" * w for w in widths))
        for row in safe_rows:
            print(_fmt(row))
        print()

    elif args.command == "delete":
        if args.dry_run:
            print(f"\n🔍 Dry run: would delete rule {args.rule_id}\n")
            return

        if not args.yes:
            answer = input(
                f"Are you sure you want to delete rule {args.rule_id}? [y/N] "
            )
            if answer not in ("y", "Y"):
                print("\nAborted.\n")
                return

        client.email_routing.rules.delete(
            zone_id=zone_id,
            rule_identifier=args.rule_id
        )
        print(
            f"\n🗑️  Email Routing Rule with ID {args.rule_id} has been "
            "deleted successfully!\n"
        )

if __name__ == "__main__":
    main()
