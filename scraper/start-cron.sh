#!/bin/sh
set -eu

CRON_SCHEDULE="${SCRAPER_CRON_SCHEDULE:-0 3 * * *}"
CRON_ENV_FILE="/app/.cron-env"
CRON_FILE="/etc/cron.d/optibot-scraper"

python - <<'PY' > "$CRON_ENV_FILE"
import os
import shlex

for key, value in sorted(os.environ.items()):
    print(f"export {key}={shlex.quote(value)}")
PY

chmod 600 "$CRON_ENV_FILE"

cat > "$CRON_FILE" <<EOF
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

${CRON_SCHEDULE} root /bin/sh /app/scraper/run-sync.sh >> /proc/1/fd/1 2>> /proc/1/fd/2
EOF

chmod 0644 "$CRON_FILE"

echo "Configured scraper cron schedule: ${CRON_SCHEDULE}"
echo "Running initial scraper sync before starting cron..."
/bin/sh /app/scraper/run-sync.sh

exec cron -f
