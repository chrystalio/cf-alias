import argparse

def main():
    parser = argparse.ArgumentParser(description="Cloudflare Email Forwarding Alias Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    add_parser = subparsers.add_parser("create", help="Create a new email alias")
    add_parser.add_argument("name", type=str, help="Name of the email alias to add")

    args = parser.parse_args()

    if  args.command == "create":
        print(f"Creating alias: {args.name}")

if __name__ == "__main__":
    main()