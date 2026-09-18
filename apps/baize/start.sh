#!/usr/bin/env bash
# Bring the local install up and open it as a fullscreen kiosk window.
set -euo pipefail
cd "$(dirname "$0")"

export LICENSE_PUBLIC_KEY="$(cat public.pem)"          # multi-line PEM -> env, newlines intact
export VITE_LICENSE_SERVER_URL="${VITE_LICENSE_SERVER_URL:-https://license.baize.pk}"

docker compose -f docker-compose.local.yml up -d

echo "→ waiting for the app…"
until curl -sf http://localhost:5000/api/branding >/dev/null 2>&1; do sleep 1; done

# Kiosk: no address bar, fullscreen. Falls back across common Chromium names.
BROWSER="$(command -v chromium || command -v chromium-browser || command -v google-chrome || command -v google-chrome-stable || echo chromium)"
"$BROWSER" --kiosk --app=http://localhost:5000 --no-first-run --disable-translate >/dev/null 2>&1 &
echo "✓ Baize is running at http://localhost:5000"