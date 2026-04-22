"""Backend configuration."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent

STATE_DB_PATH = Path(os.getenv("STATE_DB_PATH", "data/state.db"))
RUN_ARTIFACT = Path(os.getenv("RUN_ARTIFACT", "last_run.json"))
_frontend_dist_dir = os.getenv("FRONTEND_DIST_DIR", "frontend/dist").strip()
FRONTEND_DIST_DIR = (
    (ROOT_DIR / _frontend_dist_dir).resolve() if _frontend_dist_dir and not Path(_frontend_dist_dir).is_absolute()
    else Path(_frontend_dist_dir) if _frontend_dist_dir
    else None
)
ALLOWED_ORIGIN = os.getenv("CORS_ALLOW_ORIGIN", "*")
API_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
API_PORT = int(os.getenv("FLASK_PORT", "8000"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

STORE_META_KEY = "gemini_file_search_store_name"

SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
Tone: helpful, factual, concise.
Only answer using the uploaded docs.
Max 5 bullet points; else link to the doc.
Cite up to 3 "Article URL:" lines per reply."""
