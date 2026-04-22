"""Gemini File Search store operations."""
from __future__ import annotations

import os
import time
from typing import Any

from google import genai

from models import ArticleDoc
from settings import (
    FILE_SEARCH_STORE_DISPLAY_NAME,
    GEMINI_OPERATION_POLL_SECONDS,
    GEMINI_OPERATION_TIMEOUT_SECONDS,
    STORE_META_KEY,
)
from state import connect_state_db, get_metadata_value, set_metadata_value
from utils import log, object_to_dict


def make_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required.")
    return genai.Client(api_key=api_key)


def metadata_entries_for_doc(doc: ArticleDoc) -> list[dict[str, Any]]:
    return [
        {"key": "article_id", "string_value": doc.article_id},
        {"key": "article_url", "string_value": doc.url[:500]},
        {"key": "slug", "string_value": doc.slug[:500]},
        {"key": "content_hash", "string_value": doc.content_hash},
        {"key": "source_updated_at", "string_value": doc.source_updated_at[:500]},
    ]


def wait_for_operation(client: genai.Client, operation: Any, timeout_seconds: int | None = None) -> Any:
    effective_timeout = GEMINI_OPERATION_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    deadline = None if effective_timeout <= 0 else time.time() + effective_timeout
    started_at = time.time()

    while not getattr(operation, "done", False):
        now = time.time()
        waited_seconds = round(now - started_at, 1)

        if deadline is not None and now > deadline:
            raise TimeoutError(
                "Timed out waiting for Gemini operation: "
                f"{getattr(operation, 'name', 'unknown')} after {waited_seconds}s"
            )

        time.sleep(GEMINI_OPERATION_POLL_SECONDS)
        operation = client.operations.get(operation)

    if getattr(operation, "error", None):
        raise RuntimeError(f"Gemini operation failed: {object_to_dict(operation.error)}")
    return operation


def get_or_create_file_search_store(client: genai.Client, conn: Any) -> str:
    configured_name = os.getenv("GEMINI_FILE_SEARCH_STORE")
    if configured_name:
        set_metadata_value(conn, STORE_META_KEY, configured_name)
        return configured_name

    remembered_name = get_metadata_value(conn, STORE_META_KEY)
    if remembered_name:
        return remembered_name

    store = client.file_search_stores.create(config={"display_name": FILE_SEARCH_STORE_DISPLAY_NAME})
    set_metadata_value(conn, STORE_META_KEY, store.name)
    log("created_file_search_store", store_name=store.name, display_name=store.display_name)
    return store.name


def upload_doc(client: genai.Client, store_name: str, doc: ArticleDoc) -> str:
    operation = client.file_search_stores.upload_to_file_search_store(
        file_search_store_name=store_name,
        file=doc.path,
        config={
            "mime_type": "text/markdown",
            "display_name": doc.title[:128],
            "custom_metadata": metadata_entries_for_doc(doc),
        },
    )
    completed = wait_for_operation(client, operation)
    response = completed.response
    if response is None:
        raise RuntimeError(f"Upload succeeded but no Gemini response was returned for {doc.path}")

    if isinstance(response, dict):
        document_name = response.get("document_name")
    else:
        document_name = response.document_name

    if not document_name:
        raise RuntimeError(f"Upload succeeded but no Gemini document name was returned for {doc.path}")
    return document_name


def delete_document(client: genai.Client, document_name: str) -> None:
    client.file_search_stores.documents.delete(name=document_name, config={"force": True})
    log("deleted_old_document", document_name=document_name)


def get_active_store_name(conn: Any | None = None) -> str:
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
