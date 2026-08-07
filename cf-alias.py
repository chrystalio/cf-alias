import argparse
import os
import dotenv
from cloudflare import Cloudflare

dotenv.load_dotenv()

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

    if  args.command == "create":

        rule = client.email_routing.rules.create(
            zone_id=os.getenv("CF_ZONE_ID"),
            name=f"Alias for {args.name}",
            enabled=True,
            matchers=[
                {
                    "type": "literal",
                    "field": "to",
                    "value": f"{args.name}@{os.getenv('DOMAIN')}"
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
        print(f"  • Alias       : {args.name}@{os.getenv('DOMAIN')}")
        print(f"  • Forward To  : {os.getenv('DEFAULT_FORWARD_TO')}")
        print(f"  • Rule ID     : {rule.id}")
        print(f"  • Status      : Active\n")

    elif args.command == "list": 
        rules = client.email_routing.rules.list(zone_id=os.getenv("CF_ZONE_ID"))

        print("\n📜 List of Email Routing Rules 📜\n"
        "--------------------------------------------------")
        for rule in rules:
            try:
                alias_email = rule.matchers[0].value if rule.matchers else "N/A"
                destination_email = rule.actions[0].value[0] if rule.actions else "N/A"
            except (IndexError, AttributeError):
                alias_email = "Unknown"
                destination_email = "Unknown"
            print(f"  • Alias       : {alias_email}")
            print(f"  • Forward To  : {destination_email}")
            print(f"  • Rule ID     : {rule.id}")
            print(f"  • Status      : {'Active' if rule.enabled else 'Inactive'}")
            print("--------------------------------------------------")

    elif args.command == "delete":
        client.email_routing.rules.delete(
            zone_id=os.getenv("CF_ZONE_ID"),
            rule_identifier=args.rule_id
        )
        print(f"\n🗑️  Email Routing Rule with ID {args.rule_id} has been deleted successfully!\n")

if __name__ == "__main__":
    main()