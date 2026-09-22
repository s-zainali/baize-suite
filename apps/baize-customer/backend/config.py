"""Environment configuration — one place, read once."""
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
IS_PROD = os.environ.get("BAIZE_ENV", "").lower() != "development"

def _require_secret(name, weak_default=""):
    val = os.environ.get(name, "")
    if val and val != weak_default:
        return val
    if IS_PROD:
        raise RuntimeError(f"[SECURITY] {name} must be set to a strong value in production. Refusing to start.")
    return val or weak_default

JWT_SECRET   = _require_secret("CUSTOMER_JWT_SECRET", "dev-customer-secret")
CLUB_UID     = os.environ.get("CLUB_UID")               # scope to one club; None = all (dev)

# ── central (baize) connection — see central.py ──
# When set, the app talks to the baize central API instead of the local DB.
CENTRAL_API_URL = os.environ.get("CENTRAL_API_URL")     # e.g. https://central.baize.app
CENTRAL_API_KEY = os.environ.get("CENTRAL_API_KEY")

# Shared secret for signing calls to club nodes (must match each club's env).
BRIDGE_SECRET = os.environ.get("BRIDGE_SECRET", "")

# Shared admin key the licence server uses to enlist/delist clubs (registry).
REGISTRY_ADMIN_KEY = os.environ.get("REGISTRY_ADMIN_KEY", "")

CORS_ORIGINS = [o for o in os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",") if o]