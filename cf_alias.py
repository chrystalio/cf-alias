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


dotenv.load_dotenv(_find_env())

REQUIRED_ENV_VARS = ("CF_API_TOKEN", "CF_ZONE_ID", "DOMAIN", "DEFAULT_FORWARD_TO")


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

def main():
    client = Cloudflare(api_token=os.getenv("CF_API_TOKEN"))
    parser = argparse.ArgumentParser(description="Cloudflare Email Forwarding Alias Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    add_parser = subparsers.add_parser("create", help="Create a new email alias")
    add_parser.add_argument("name", type=str, help="Name of the email alias to add")

    subparsers.add_parser("list", help="list of email aliases")

    delete_parser = subparsers.add_parser("delete", help="Delete an existing email alias")
    delete_parser.add_argument("rule_id", type=str, help="ID of the email alias to delete")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    require_env()

    if  args.command == "create":

        target_email = f"{args.name}@{os.getenv('DOMAIN')}"
        rules = client.email_routing.rules.list(zone_id=os.getenv("CF_ZONE_ID"))

        for rule in rules:
            existing_alias = rule.matchers[0].value if rule.matchers else None
            if existing_alias == target_email:
                print(f"\n⚠️  Alias '{target_email}' already exists. No new rule created.\n")
                return

        rule = client.email_routing.rules.create(
            zone_id=os.getenv("CF_ZONE_ID"),
            name=f"Alias for {args.name}",
            enabled=True,
            matchers=[
                {
                    "type": "literal",
                    "field": "to",
                    "value": target_email
                }
            ],
            actions=[
                {
                    "type": "forward",
                    "value": [os.getenv("DEFAULT_FORWARD_TO")]
                }
            ]
        )
        print("\n✨ Email Routing Rule Created Successfully! ✨")
        print(f"  • Alias       : {target_email}")
        print(f"  • Forward To  : {os.getenv('DEFAULT_FORWARD_TO')}")
        print(f"  • Rule ID     : {rule.id}")
        print(f"  • Status      : Active\n")

    elif args.command == "list":
        rules = list(client.email_routing.rules.list(zone_id=os.getenv("CF_ZONE_ID")))

        if not rules:
            print("\n📜 No email routing rules found for this zone.\n")
            return

        def _cell(value, missing="Unknown"):
            """Coerce a rule field into a printable string. Any None / missing → 'Unknown'."""
            if value is None:
                return missing
            return str(value) if value != "" else missing

        rows = []
        for rule in rules:
            try:
                alias_email = _cell(rule.matchers[0].value, "N/A") if rule.matchers else "N/A"
                destination_email = (
                    _cell(rule.actions[0].value[0], "N/A") if rule.actions else "N/A"
                )
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
            return value if isinstance(value, str) else str(value) if value != "" else missing

        safe_rows = [
            tuple(_safe_cell(c) for c in row) for row in rows
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
        client.email_routing.rules.delete(
            zone_id=os.getenv("CF_ZONE_ID"),
            rule_identifier=args.rule_id
        )
        print(f"\n🗑️  Email Routing Rule with ID {args.rule_id} has been deleted successfully!\n")

if __name__ == "__main__":
    main()