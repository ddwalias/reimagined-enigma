"""Scraper configuration."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

HELP_CENTER_HOST = "https://support.optisigns.com"
LOCALE = "en-us"
OUT_DIR = Path(os.getenv("OUT_DIR", "data/markdown"))
STATE_DB_PATH = Path(os.getenv("STATE_DB_PATH", "data/state.db"))
RUN_ARTIFACT = Path(os.getenv("RUN_ARTIFACT", "last_run.json"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FILE_SEARCH_STORE_DISPLAY_NAME = "optibot-docs"
GEMINI_OPERATION_TIMEOUT_SECONDS = 1800
GEMINI_OPERATION_POLL_SECONDS = 5.0

STORE_META_KEY = "gemini_file_search_store_name"

SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
- Tone: helpful, factual, concise.
- Only answer using the uploaded docs.
- Max 5 bullet points; else link to the doc.
- Cite up to 3 "Article URL:" lines per reply."""
