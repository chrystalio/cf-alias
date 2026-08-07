import argparse
import os
import dotenv
from cloudflare import Cloudflare

dotenv.load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Cloudflare Email Forwarding Alias Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    add_parser = subparsers.add_parser("create", help="Create a new email alias")
    add_parser.add_argument("name", type=str, help="Name of the email alias to add")

    args = parser.parse_args()

    if  args.command == "create":

        client = Cloudflare(api_token=os.getenv("CF_API_TOKEN"))

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

if __name__ == "__main__":
    main()