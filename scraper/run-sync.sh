#!/bin/sh
set -eu

if [ -f /app/.cron-env ]; then
  # shellcheck disable=SC1091
  . /app/.cron-env
fi

cd /app
python scraper/main.py
