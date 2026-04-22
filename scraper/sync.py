"""End-to-end sync orchestration for scraping and Gemini indexing."""
from __future__ import annotations

import json
import traceback
from dataclasses import asdict
from typing import Any

from file_search import delete_document, get_or_create_file_search_store, make_gemini_client, upload_doc
from scraper import fetch_articles, write_markdown
from settings import (
    GEMINI_MODEL,
    GEMINI_OPERATION_POLL_SECONDS,
    GEMINI_OPERATION_TIMEOUT_SECONDS,
    LOCALE,
    RUN_ARTIFACT,
    STATE_DB_PATH,
    SYSTEM_PROMPT,
)
from state import connect_state_db, load_article_state, upsert_article_state
from utils import log, now_utc_iso


def sync_to_gemini(client: Any, conn: Any, store_name: str, docs: list[Any]) -> dict[str, Any]:
    existing = load_article_state(conn)
    seen_at = now_utc_iso()

    added = 0
    updated = 0
    skipped = 0
    uploaded_documents: list[dict[str, str]] = []

    for doc in docs:
        row = existing.get(doc.article_id)
        existing_hash = row["content_hash"] if row else None
        existing_document_name = row["gemini_document_name"] if row else None
        existing_store_name = row["gemini_file_search_store_name"] if row else None

        if (
            row
            and existing_hash == doc.content_hash
            and existing_document_name
            and existing_store_name == store_name
        ):
            skipped += 1
            upsert_article_state(conn, doc, store_name, existing_document_name, seen_at)
            log("skip_unchanged", article_id=doc.article_id, title=doc.title)
            continue

        new_document_name = upload_doc(client, store_name, doc)
        if row and existing_store_name == store_name:
            updated += 1
            action = "updated"
        else:
            added += 1
            action = "added"

        if existing_document_name and existing_store_name == store_name:
            try:
                delete_document(client, existing_document_name)
            except Exception as exc:
                try:
                    delete_document(client, new_document_name)
                except Exception as rollback_exc:
                    log(
                        "rollback_delete_failed",
                        article_id=doc.article_id,
                        new_document_name=new_document_name,
                        error=str(rollback_exc),
                        exc_type=type(rollback_exc).__name__,
                    )
                raise RuntimeError(
                    f"Failed to replace Gemini document for article {doc.article_id}: {exc}"
                ) from exc

        upsert_article_state(conn, doc, store_name, new_document_name, seen_at)
        uploaded_documents.append({"article_id": doc.article_id, "document_name": new_document_name})
        log(
            action,
            article_id=doc.article_id,
            title=doc.title,
            document_name=new_document_name,
        )

    return {
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "files_total": len(docs),
        "uploaded_documents": uploaded_documents,
    }


def sync_once(started_at: str) -> dict[str, Any]:
    articles = fetch_articles()
    docs = write_markdown(articles)

    client = make_gemini_client()
    conn = connect_state_db()
    try:
        store_name = get_or_create_file_search_store(client, conn)
        sync_result = sync_to_gemini(client, conn, store_name, docs)
    finally:
        conn.close()

    artifact = {
        "started_at": started_at,
        "finished_at": now_utc_iso(),
        "gemini_model": GEMINI_MODEL,
        "file_search_store_name": store_name,
        "system_prompt": SYSTEM_PROMPT,
        "state_db_path": str(STATE_DB_PATH),
        "docs": [asdict(doc) for doc in docs],
        **sync_result,
    }
    RUN_ARTIFACT.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    return artifact


def run_sync_cli() -> int:
    started_at = now_utc_iso()
    try:
        log(
            "run_started",
            locale=LOCALE,
            gemini_model=GEMINI_MODEL,
            operation_timeout_seconds=GEMINI_OPERATION_TIMEOUT_SECONDS,
            operation_poll_seconds=GEMINI_OPERATION_POLL_SECONDS,
        )
        artifact = sync_once(started_at)
        log(
            "run_complete",
            added=artifact["added"],
            updated=artifact["updated"],
            skipped=artifact["skipped"],
            file_search_store_name=artifact["file_search_store_name"],
            artifact=str(RUN_ARTIFACT),
        )
        return 0
    except Exception as exc:
        log(
            "run_failed",
            error=str(exc),
            exc_type=type(exc).__name__,
            traceback=traceback.format_exc(),
        )
        return 1
