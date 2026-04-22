"""SQLite-backed local state for sync bookkeeping."""
from __future__ import annotations

import sqlite3

from models import ArticleDoc
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


def set_metadata_value(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO metadata(key, value) VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )
    conn.commit()


def load_article_state(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    rows = conn.execute("SELECT * FROM article_state").fetchall()
    return {row["article_id"]: row for row in rows}


def upsert_article_state(
    conn: sqlite3.Connection,
    doc: ArticleDoc,
    store_name: str,
    document_name: str | None,
    seen_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO article_state(
            article_id,
            title,
            slug,
            article_url,
            markdown_path,
            content_hash,
            source_updated_at,
            last_seen_at,
            gemini_document_name,
            gemini_file_search_store_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(article_id) DO UPDATE SET
            title = excluded.title,
            slug = excluded.slug,
            article_url = excluded.article_url,
            markdown_path = excluded.markdown_path,
            content_hash = excluded.content_hash,
            source_updated_at = excluded.source_updated_at,
            last_seen_at = excluded.last_seen_at,
            gemini_document_name = excluded.gemini_document_name,
            gemini_file_search_store_name = excluded.gemini_file_search_store_name
        """,
        (
            doc.article_id,
            doc.title,
            doc.slug,
            doc.url,
            doc.path,
            doc.content_hash,
            doc.source_updated_at,
            seen_at,
            document_name,
            store_name,
        ),
    )
    conn.commit()
