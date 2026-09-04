"""Interactive arrow-key menu TUI for cf-alias."""
from __future__ import annotations

import questionary
from questionary import Choice
from rich.console import Console
from rich.table import Table

from cf_alias import db
from cf_alias.generator import generate_alias_name
from cf_alias.main import (
    HEADERS,
    AppContext,
    _cell,
    _rule_to_row,
    _safe_cell,
)

console = Console()


def _fetch_rules(ctx: AppContext) -> list[tuple[str, ...]]:
    page = ctx.client.email_routing.rules.list(zone_id=ctx.zone_id)
    return [
        _rule_to_row(r, db.get_category(_cell(r.id)) or "") for r in list(page)
    ]


def _render_rules(ctx: AppContext, title: str = "Email Routing Rules") -> None:
    rules = _fetch_rules(ctx)
    if not rules:
        console.print("\n[yellow]No email routing rules found.[/yellow]\n")
        return
    table = Table(title=title, show_lines=True)
    for h in HEADERS:
        table.add_column(h, style="cyan")
    for row in rules:
        cells = [_safe_cell(c) for c in row]
        # Replace the STATUS cell (index 3) with a coloured icon
        cells[3] = _status_icon(cells[3] == "Active")
        table.add_row(*cells)
    console.print(table)


# Block-letter ASCII art for the banner. The shape on the right spells
# "ALIAS" using mixed-width Unicode box-drawing characters.
_BANNER_ART = [
    "[bold cyan]██████╗ ███████╗██╗   ██╗    ███████╗ ██████╗ ██╗   ██╗███████╗███████╗████████╗[/bold cyan]",  # noqa: E501
    "[bold cyan]██╔══██╗██╔════╝██║   ██║    ██╔════╝██╔═══██╗██║   ██║╭──────╮╭────────╮╰────────╯[/bold cyan]",  # noqa: E501
    "[bold cyan]██████╔╝█████╗  ██║   ██║    █████╗  ██║   ██║╰─────╯│  ██╗  ██╗  ██████╗ ╰─────╮[/bold cyan]",  # noqa: E501
    "[bold cyan]██╔══██╗██╔══╝  ╚██╗ ██╔╝    ██╔══╝  ██║   ██║        ╰──╯  ╰──╯  ╰─────╯       ╰─────╮[/bold cyan]",  # noqa: E501
    "[bold cyan]██║  ██║███████╗ ╚████╔╝     ███████╗╚██████╔╝                                  ╰────────╮[/bold cyan]",  # noqa: E501
    "[bold cyan]╚═╝  ╚═╝╚══════╝  ╚═══╝      ╚══════╝ ╚═════╝                                          [/bold cyan]",  # noqa: E501
]


def _WELCOME_BANNER(ctx: AppContext) -> None:
    """Render a block-letter ASCII art banner."""
    console.print()
    for line in _BANNER_ART:
        console.print(f"  {line}")
    console.print(f"\n  [dim]Domain:[/dim]  {ctx.domain}")
    console.print()


def _status_icon(enabled: bool) -> str:
    """Return ● for active, ○ for inactive."""
    return "[green]●[/green] Active" if enabled else "[dim]○[/dim] Inactive"


def _menu_create(ctx: AppContext) -> None:
    choice = questionary.select(
        "How do you want to create the alias?",
        choices=[
            Choice(title="Custom name", value="custom"),
            Choice(title="Generate random name", value="generate"),
            Choice(title="<- Cancel", value=None),
        ],
        qmark=">>",
    ).ask()
    if choice is None or choice == "cancel":
        return

    if choice == "generate":
        name = None
        while True:
            name = generate_alias_name()
            console.print(f"\n  [cyan]{name}[/cyan]\n")
            decision = questionary.select(
                "Happy with this name?",
                choices=[
                    Choice(title="Accept", value="accept"),
                    Choice(title="Regenerate", value="regenerate"),
                    Choice(title="Cancel", value="cancel"),
                ],
                qmark=">>",
            ).ask()
            if decision == "accept":
                break
            if decision == "cancel":
                return
    else:
        name = questionary.text(
            "Alias name (the part before @):",
            validate=lambda text: len(text) > 0 or "Name cannot be empty",
        ).ask()
        if name is None:
            return

    category = questionary.text(
        "Category (optional, press Enter to skip):",
        default="",
    ).ask()
    if category is None:
        return

    target_email = f"{name}@{ctx.domain}"

    # Check for existing rule first (idempotent behaviour mirrors CLI create)
    page = ctx.client.email_routing.rules.list(zone_id=ctx.zone_id)
    while True:
        for rule in page:
            existing = rule.matchers[0].value if rule.matchers else None
            if existing == target_email:
                first_action = rule.actions[0] if rule.actions else None
                existing_dest = None
                if first_action is not None and first_action.value:
                    existing_dest = first_action.value[0]
                if existing_dest == ctx.default_forward_to:
                    console.print(
                        f"[yellow]Alias '{target_email}' already exists "
                        f"and forwards to '{ctx.default_forward_to}'.[/yellow]"
                    )
                else:
                    console.print(
                        f"[yellow]Alias '{target_email}' already exists "
                        f"but forwards to '{existing_dest}', not "
                        f"'{ctx.default_forward_to}'.[/yellow]"
                    )
                return
        if page.has_next_page():
            page = page.get_next_page()
        else:
            break

    rule = ctx.client.email_routing.rules.create(
        zone_id=ctx.zone_id,
        name=f"Alias for {name}",
        enabled=True,
        matchers=[
            {"type": "literal", "field": "to", "value": target_email},
        ],
        actions=[
            {"type": "forward", "value": [ctx.default_forward_to]},
        ],
    )
    if category and rule and rule.id:
        db.set_category(rule.id, category)
    console.print(f"[green]Created alias {target_email}[/green]")


def _menu_list(ctx: AppContext) -> None:
    _render_rules(ctx)


def _menu_delete(ctx: AppContext) -> None:
    rules = _fetch_rules(ctx)
    if not rules:
        console.print("[yellow]No aliases to delete.[/yellow]")
        return
    choices = [
        Choice(
            title=f"{row[0]}  ->  {row[1]}  ({row[2]})",
            value=row[2],
        )
        for row in rules
    ]
    choices.append(Choice(title="<- Cancel", value=None))
    rule_id = questionary.select(
        "Select alias to delete:",
        choices=choices,
    ).ask()
    if rule_id is None:
        return
    if not questionary.confirm(
        f"Really delete alias with ID {rule_id}?", default=False
    ).ask():
        return
    ctx.client.email_routing.rules.delete(
        zone_id=ctx.zone_id, rule_identifier=rule_id
    )
    db.clear_category(rule_id)
    console.print(f"[green]Deleted rule {rule_id}[/green]")


def _menu_categorize(ctx: AppContext) -> None:
    rules = _fetch_rules(ctx)
    if not rules:
        console.print("[yellow]No aliases to categorize.[/yellow]")
        return
    choices = [
        Choice(
            title=f"{row[0]}  (current: {db.get_category(row[2]) or '—'})",
            value=row[2],
        )
        for row in rules
    ]
    choices.append(Choice(title="<- Cancel", value=None))
    rule_id = questionary.select(
        "Select alias to categorize:",
        choices=choices,
    ).ask()
    if rule_id is None:
        return
    action = questionary.select(
        f"What do you want to do with {rule_id}?",
        choices=[
            Choice(title="Set category", value="set"),
            Choice(title="Clear category", value="clear"),
            Choice(title="<- Cancel", value=None),
        ],
    ).ask()
    if action == "set":
        cat = questionary.text(
            "Category name:",
            validate=lambda t: len(t) > 0 or "Cannot be empty",
        ).ask()
        if cat:
            db.set_category(rule_id, cat)
            console.print(f"[green]Categorized as '{cat}'[/green]")
    elif action == "clear":
        db.clear_category(rule_id)
        console.print("[green]Category cleared[/green]")


def launch_tui(ctx: AppContext) -> None:
    """Main menu loop. Returns when the user selects Quit."""
    _WELCOME_BANNER(ctx)
    actions = {
        "create": _menu_create,
        "list": _menu_list,
        "delete": _menu_delete,
        "categorize": _menu_categorize,
    }
    while True:
        choice = questionary.select(
            "What do you want to do?",
            choices=[
                Choice(title="Create alias", value="create"),
                Choice(title="List aliases", value="list"),
                Choice(title="Delete alias", value="delete"),
                Choice(title="Categorize alias", value="categorize"),
                Choice(title="Quit", value="quit"),
            ],
            qmark=">>",
        ).ask()
        if choice is None or choice == "quit":
            console.print("Bye!")
            return
        try:
            actions[choice](ctx)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
        questionary.press_any_key_to_continue(
            "Press any key to return to menu..."
        ).ask()
