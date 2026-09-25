"""Club asset storage on a CDN (Cloudinary).

Why: club logos must survive restarts/redeploys (Render's disk is ephemeral)
and must be reachable by every app (club, customer, admin) without depending on
the club node's own public_url. Storing bytes in Postgres would bloat the DB as
clubs grow, so assets go to a dedicated image CDN instead and we keep only a URL.

The logo URL is DETERMINISTIC from the club uuid
(`.../image/upload/baize/logos/<club_uid>`), so any app can build it from the
uuid alone — no propagation, no registry column, no public_url. If the club has
never uploaded a logo the URL simply 404s and the UI falls back to an initial.

Config (env): CLOUDINARY_CLOUD_NAME (needed by every app to build URLs),
plus CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET (club only, to upload).
"""
import os
import time
import hashlib

CLOUD = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
KEY = os.environ.get("CLOUDINARY_API_KEY", "").strip()
SECRET = os.environ.get("CLOUDINARY_API_SECRET", "").strip()
LOGO_FOLDER = "baize/logos"


def cdn_configured():
    """True when this node can UPLOAD to the CDN (needs the secret)."""
    return bool(CLOUD and KEY and SECRET)


def logo_public_id(club_uid):
    return f"{LOGO_FOLDER}/{club_uid}"


def cdn_logo_url(club_uid):
    """The deterministic, absolute, cache-busting-free public URL for a club's
    logo. Requires only the cloud name, so every app can build it. Returns None
    when no cloud is configured (caller falls back to legacy behaviour)."""
    if not CLOUD or not club_uid:
        return None
    return f"https://res.cloudinary.com/{CLOUD}/image/upload/{LOGO_FOLDER}/{club_uid}"


def upload_logo_to_cdn(club_uid, raw, ext="png"):
    """Upload (overwrite) a club's logo to the CDN under a stable public_id and
    return its absolute URL. Returns None if the CDN isn't configured so the
    caller can fall back to local disk in dev. Raises only on a genuine CDN
    error the caller should surface."""
    if not cdn_configured():
        return None
    import httpx
    ts = str(int(time.time()))
    pid = logo_public_id(club_uid)
    # Cloudinary signs the SHA1 of the alphabetically-sorted params + secret.
    to_sign = f"invalidate=true&overwrite=true&public_id={pid}&timestamp={ts}{SECRET}"
    sig = hashlib.sha1(to_sign.encode()).hexdigest()
    data = {
        "api_key": KEY,
        "timestamp": ts,
        "public_id": pid,
        "overwrite": "true",
        "invalidate": "true",   # purge the old edge cache on re-upload
        "signature": sig,
    }
    files = {"file": (f"logo.{ext}", raw)}
    r = httpx.post(
        f"https://api.cloudinary.com/v1_1/{CLOUD}/image/upload",
        data=data, files=files, timeout=20.0,
    )
    r.raise_for_status()
    return r.json().get("secure_url") or cdn_logo_url(club_uid)