#!/usr/bin/env sh
# Container entrypoint: bring the schema up, seed first-run data, then serve.
set -e

cd /app/backend
export FLASK_APP=api/index.py

: "${PORT:=5000}"

echo "→ waiting for the database"
python - <<'PY'
import os, time
from urllib.parse import urlparse, urlunparse, quote_plus
from sqlalchemy.engine import make_url

raw_url = os.environ.get("DATABASE_URL")
if not raw_url:
    raise SystemExit("ERROR: DATABASE_URL environment variable is completely empty or missing!")

raw_url = raw_url.strip()

# Normalize scheme
if raw_url.startswith("postgres://"):
    raw_url = "postgresql+psycopg2://" + raw_url[11:]
elif raw_url.startswith("postgresql://") and "+psycopg" not in raw_url:
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Safely parse and URL-encode the password to handle special symbols (#, @, etc.)
try:
    parsed = urlparse(raw_url)
    if parsed.password:
        encoded_password = quote_plus(parsed.password)
        # Reconstruct netloc with the encoded password
        user_info = parsed.username if parsed.username else ""
        if encoded_password:
            user_info += f":{encoded_password}"
        
        netloc = f"{user_info}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
            
        parsed = parsed._replace(netloc=netloc)
        final_url = urlunparse(parsed)
    else:
        final_url = raw_url
except Exception as parse_err:
    print(f"Warning during manual URL parsing: {parse_err}, falling back to raw URL.")
    final_url = raw_url

last = None
for i in range(30):
    try:
        url_obj = make_url(final_url)
        engine = __import__('sqlalchemy').create_engine(url_obj)
        conn = engine.connect()
        conn.close()
        print("  database is ready")
        break
    except Exception as exc:
        last = exc
        print(f"  [Attempt {i+1}/30] waiting for database ({exc.__class__.__name__}: {exc})")
        time.sleep(2)
else:
    raise SystemExit(f"database not reachable after 30 attempts: {last}")
PY

echo "→ applying migrations (flask db upgrade)"
flask db upgrade

echo "→ seeding first-run data (flask seed)"
flask seed

echo "→ starting server on :$PORT"
exec python api/index.py