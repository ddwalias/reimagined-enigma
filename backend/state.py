"""Backend SQLite helpers for store lookup and status reporting."""
from __future__ import annotations

import sqlite3

from settings import STATE_DB_PATH


def connect_state_db() -> sqlite3.Connection:
    STATE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(STATE_DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS article_state (
            article_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            slug TEXT NOT NULL,
            article_url TEXT NOT NULL,
            markdown_path TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            source_updated_at TEXT,
            last_seen_at TEXT NOT NULL,
            gemini_document_name TEXT,
            gemini_file_search_store_name TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.commit()


def get_metadata_value(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None
