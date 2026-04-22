"""Flask JSON API for OptiBot, with optional static serving for a built frontend."""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from query import ask_messages, stream_messages
from settings import (
    ALLOWED_ORIGIN,
    API_HOST,
    API_PORT,
    FRONTEND_DIST_DIR,
    GEMINI_MODEL,
    RUN_ARTIFACT,
    STATE_DB_PATH,
)

app = Flask(__name__)


def apply_cors(response: Any) -> Any:
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


app.after_request(apply_cors)


def json_error(message: str, status: int = 400) -> Any:
    response = jsonify({"error": message})
    response.status_code = status
    return response


def sse_event(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def parse_json_request() -> dict[str, Any]:
    if not request.is_json:
        raise UnsupportedMediaType("Expected application/json request body.")

    payload = request.get_json()
    if not isinstance(payload, dict):
        raise BadRequest("JSON body must be an object.")
    return payload


def state_summary() -> dict[str, Any]:
    article_count = 0
    if STATE_DB_PATH.exists():
        conn = sqlite3.connect(STATE_DB_PATH)
        try:
            row = conn.execute("SELECT COUNT(*) FROM article_state").fetchone()
            article_count = int(row[0]) if row else 0
        finally:
            conn.close()

    last_run = None
    last_run_error = None
    if RUN_ARTIFACT.exists():
        try:
            last_run = json.loads(RUN_ARTIFACT.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            last_run_error = str(exc)
            app.logger.warning("Failed to parse %s: %s", RUN_ARTIFACT, exc)

    summary = {
        "gemini_model": GEMINI_MODEL,
        "state_db_path": str(STATE_DB_PATH),
        "article_count": article_count,
        "last_run": last_run,
    }
    if last_run_error:
        summary["last_run_error"] = last_run_error
    return summary


@app.route("/api/health", methods=["GET", "OPTIONS"])
def health() -> Any:
    if request.method == "OPTIONS":
        return ("", 204)
    return jsonify({"ok": True, "service": "optibot-api"})


@app.route("/api/status", methods=["GET", "OPTIONS"])
def status() -> Any:
    if request.method == "OPTIONS":
        return ("", 204)
    return jsonify(state_summary())


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat() -> Any:
    if request.method == "OPTIONS":
        return ("", 204)

    try:
        payload = parse_json_request()
    except (BadRequest, UnsupportedMediaType) as exc:
        return json_error(exc.description, exc.code or 400)

    messages = payload.get("messages")
    if not isinstance(messages, list):
        return json_error("Invalid request: messages array required.", 400)

    try:
        result = ask_messages(messages)
        return jsonify(result)
    except ValueError as exc:
        return json_error(str(exc), 400)
    except Exception as exc:
        app.logger.exception("Chat request failed")
        return json_error("Internal server error.", 500)


@app.route("/api/chat/stream", methods=["POST", "OPTIONS"])
def chat_stream() -> Any:
    if request.method == "OPTIONS":
        return ("", 204)

    try:
        payload = parse_json_request()
    except (BadRequest, UnsupportedMediaType) as exc:
        return json_error(exc.description, exc.code or 400)

    messages = payload.get("messages")
    if not isinstance(messages, list):
        return json_error("Invalid request: messages array required.", 400)

    def generate() -> Any:
        try:
            for event in stream_messages(messages):
                yield sse_event(event["type"], event)
        except ValueError as exc:
            yield sse_event("error", {"error": str(exc)})
        except Exception as exc:
            app.logger.exception("Streaming chat request failed")
            yield sse_event("error", {"error": "Internal server error."})

    response = Response(stream_with_context(generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@app.get("/")
def root() -> Any:
    if FRONTEND_DIST_DIR and FRONTEND_DIST_DIR.exists():
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")
    return jsonify(
        {
            "service": "optibot-api",
            "endpoints": ["/api/health", "/api/status", "/api/chat", "/api/chat/stream"],
            "frontend_dist_dir": str(FRONTEND_DIST_DIR) if FRONTEND_DIST_DIR else None,
        }
    )


@app.get("/<path:path>")
def static_files(path: str) -> Any:
    if not FRONTEND_DIST_DIR or not FRONTEND_DIST_DIR.exists():
        return json_error("Not found.", 404)

    candidate = FRONTEND_DIST_DIR / path
    if candidate.exists() and candidate.is_file():
        return send_from_directory(FRONTEND_DIST_DIR, path)
    return send_from_directory(FRONTEND_DIST_DIR, "index.html")


if __name__ == "__main__":
    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=False,
    )
