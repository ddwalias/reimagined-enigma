"""CLI entry point for the OptiBot scraper + Gemini sync job."""
from __future__ import annotations

from sync import run_sync_cli


def main() -> int:
    return run_sync_cli()


if __name__ == "__main__":
    raise SystemExit(main())
