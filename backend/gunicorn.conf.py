"""Gunicorn settings for the backend API."""
from __future__ import annotations

import os


bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
chdir = "/app/backend"
workers = int(os.getenv("GUNICORN_WORKERS", "2"))

# SSE requests can block while Gemini streams tokens back. Threaded workers
# avoid Gunicorn's sync-worker timeout path during those long-lived requests.
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")
threads = int(os.getenv("GUNICORN_THREADS", "4"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "180"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
