"""Backend-only Gemini File Search helpers."""
from __future__ import annotations

import os

from google import genai

from settings import STORE_META_KEY
from state import connect_state_db, get_metadata_value


def make_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required.")
    return genai.Client(api_key=api_key)


def get_active_store_name(conn: object | None = None) -> str:
    configured_name = os.getenv("GEMINI_FILE_SEARCH_STORE")
    if configured_name:
        return configured_name

    owns_connection = conn is None
    if conn is None:
        conn = connect_state_db()

    try:
        remembered_name = get_metadata_value(conn, STORE_META_KEY)
        if not remembered_name:
            raise RuntimeError(
                "No Gemini File Search store configured. Run `python scraper/main.py` first "
                "or set GEMINI_FILE_SEARCH_STORE."
            )
        return remembered_name
    finally:
        if owns_connection:
            conn.close()
