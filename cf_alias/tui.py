"""Interactive Textual TUI for browsing and editing Cloudflare email aliases."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Input, Static

if TYPE_CHECKING:
    from cf_alias.main import AppContext

# Reuse from main.py
from cf_alias import db
from cf_alias.main import HEADERS, _cell, _rule_to_row


class CategoryModal(ModalScreen[str | None]):
    """Modal to edit the category for a rule."""

    def __init__(self, rule_id: str, current_category: str) -> None:
        super().__init__()
        self.rule_id = rule_id
        self.current_category = current_category or ""

    def compose(self) -> ComposeResult:
        yield Static(
            f"Category for rule {self.rule_id}:", id="label"
        )
        yield Input(
            value=self.current_category,
            id="category-input",
            placeholder="Enter category...",
        )
        yield Static("Enter to save · Esc to cancel", id="hint")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value or None)


class ConfirmDeleteModal(ModalScreen[bool]):
    """Modal to confirm rule deletion."""

    def __init__(self, rule_id: str, alias: str) -> None:
        super().__init__()
        self.rule_id = rule_id
        self.alias = alias

    def compose(self) -> ComposeResult:
        yield Static(f"Delete alias {self.alias}?", id="label")
        yield Static(f"Rule ID: {self.rule_id}", id="rule-id")
        yield Static("y / n", id="hint")

    def key_y(self) -> None:
        self.dismiss(True)

    def key_n(self) -> None:
        self.dismiss(False)


class AliasApp(App):
    """Interactive alias browser and editor."""

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "cycle_sort", "Sort", show=True),
        Binding("c", "edit_category", "Category", show=True),
        Binding("d", "delete_rule", "Delete", show=True),
    ]

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self._all_rows: list[tuple[str, ...]] = []
        self._filter_text: str = ""
        self._sort_col: int = 0  # column index
        self._sort_dir: bool = True  # True = asc
        self._loading: bool = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(
            placeholder="Filter aliases (ESC to clear)...",
            id="filter",
        )
        yield DataTable(
            id="grid",
            cursor_type="row",
            zebra_stripes=True,
        )
        yield Footer()

    def on_mount(self) -> None:
        grid = self.query_one("#grid", DataTable)
        for i, header in enumerate(HEADERS):
            grid.add_column(header, key=str(i))
        grid.sort("0")  # initial sort
        self.run_worker(self._load_rules, exclusive=True)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._filter_text = event.value
        self._render_rows()

    def on_input_pressed(self, event: Input.Pressed) -> None:  # type: ignore[reportIncompatibleMethodOverride]
        # ESC in filter clears it
        pass

    def action_refresh(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.run_worker(self._load_rules, exclusive=True)

    def _sync_fetch_rules(self) -> list[tuple[str, ...]]:
        page = self.ctx.client.email_routing.rules.list(zone_id=self.ctx.zone_id)
        return [_rule_to_row(r, db.get_category(_cell(r.id)) or "") for r in list(page)]

    async def _load_rules(self) -> None:
        self._all_rows = await asyncio.to_thread(self._sync_fetch_rules)
        self._loading = False
        self._render_rows()

    def _render_rows(self) -> None:
        grid = self.query_one("#grid", DataTable)
        # Filter
        filtered = self._all_rows
        if self._filter_text:
            q = self._filter_text.lower()
            filtered = [r for r in filtered if any(q in str(c).lower() for c in r)]
        # Sort
        col = self._sort_col
        rev = not self._sort_dir
        filtered = sorted(filtered, key=lambda r: str(r[col]).lower(), reverse=rev)
        # Clear and populate
        grid.clear()
        for row in filtered:
            grid.add_row(*row, key=row[2])  # row_key = rule_id

    def action_cycle_sort(self) -> None:
        self._sort_col = (self._sort_col + 1) % len(HEADERS)
        self._sort_dir = True
        self._render_rows()

    def action_edit_category(self) -> None:
        grid = self.query_one("#grid", DataTable)
        cursor = grid.cursor_row
        if cursor is None or cursor >= len(self._all_rows):
            return
        # Reconstruct filtered list to find the selected row's rule_id
        filtered = self._get_filtered_sorted()
        if cursor >= len(filtered):
            return
        rule_id = filtered[cursor][2]
        current = db.get_category(rule_id) or ""
        def _save(result: str | None) -> None:
            if result is not None:
                db.set_category(rule_id, result)
                self.action_refresh()
        self.push_screen(CategoryModal(rule_id, current), _save)

    def action_delete_rule(self) -> None:
        grid = self.query_one("#grid", DataTable)
        cursor = grid.cursor_row
        if cursor is None:
            return
        filtered = self._get_filtered_sorted()
        if cursor >= len(filtered):
            return
        rule_id = filtered[cursor][2]
        alias = filtered[cursor][0]

        def _confirm(result: bool | None) -> None:
            if result:
                self.ctx.client.email_routing.rules.delete(
                    zone_id=self.ctx.zone_id,
                    rule_identifier=rule_id,
                )
                db.clear_category(rule_id)
                self.action_refresh()

        self.push_screen(ConfirmDeleteModal(rule_id, alias), _confirm)

    def _get_filtered_sorted(self) -> list[tuple[str, ...]]:
        filtered = self._all_rows
        if self._filter_text:
            q = self._filter_text.lower()
            filtered = [r for r in filtered if any(q in str(c).lower() for c in r)]
        col = self._sort_col
        rev = not self._sort_dir
        return sorted(filtered, key=lambda r: str(r[col]).lower(), reverse=rev)


def launch_tui(ctx: AppContext) -> None:
    """Entry point registered as the `tui` subcommand."""
    app = AliasApp(ctx)
    app.run()
