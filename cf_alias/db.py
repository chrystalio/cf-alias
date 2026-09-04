"""SQLite persistence for alias categories."""

from __future__ import annotations

import os
import sqlite3
import sys
import threading
from pathlib import Path

# Module-level singleton connection (lazily initialized on first use)
_conn: sqlite3.Connection | None = None
_lock = threading.Lock()


def _db_path() -> Path:
    """Cross-platform location for the categories database.

    Priority: $CF_ALIAS_DB if set → ~/.config/cf-alias/categories.db (Linux/macOS XDG)
    → %APPDATA%\\cf-alias\\categories.db (Windows).
    """
    override = os.environ.get("CF_ALIAS_DB")
    if override:
        return Path(override)

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "cf-alias" / "categories.db"

    config_dir = Path.home() / ".config" / "cf-alias"
    # Ensure the directory exists on first use
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "categories.db"


def _get_conn() -> sqlite3.Connection:
    """Get or create the database connection with Row factory enabled."""
    global _conn
    if _conn is None:
        db_path = _db_path()
        # Ensure parent directory exists (especially on first run)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False allows the connection to be used from
        # worker threads (e.g. asyncio.to_thread in the TUI). Concurrent
        # access is serialised by `_lock` in the write helpers below.
        _conn = sqlite3.connect(db_path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row

        # Create tables if they don't exist
        with _lock:
            _conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS alias_categories (
                    rule_id TEXT PRIMARY KEY,
                    category TEXT,
                    set_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_category ON alias_categories(category);
                """
            )
            _conn.commit()

    return _conn


def get_category(rule_id: str) -> str | None:
    """Return the category for a rule_id, or None if not set."""
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT category FROM alias_categories WHERE rule_id = ?", (rule_id,)
    )
    row = cursor.fetchone()
    return row["category"] if row else None


def set_category(rule_id: str, category: str) -> None:
    """Upsert a category for a rule_id."""
    conn = _get_conn()
    with _lock:
        conn.execute(
            """
            INSERT INTO alias_categories (rule_id, category)
            VALUES (?, ?)
            ON CONFLICT(rule_id) DO UPDATE SET category = excluded.category
            """,
            (rule_id, category),
        )
        conn.commit()


def clear_category(rule_id: str) -> None:
    """Delete the category row for a rule_id."""
    conn = _get_conn()
    with _lock:
        conn.execute("DELETE FROM alias_categories WHERE rule_id = ?", (rule_id,))
        conn.commit()


def list_by_category(category: str) -> list[str]:
    """Return a list of rule_ids with the given category."""
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT rule_id FROM alias_categories WHERE category = ?", (category,)
    )
    return [row["rule_id"] for row in cursor.fetchall()]
