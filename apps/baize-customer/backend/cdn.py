"""Deterministic CDN URLs for club assets (customer side — read-only).

The club uploads its logo to Cloudinary under a stable public_id keyed by the
club uuid, so the customer app can build the exact same URL from the uuid alone
— no registry column, no public_url, no propagation. A club with no logo simply
404s and the UI falls back to an initial.

Config (env): CLOUDINARY_CLOUD_NAME — the same cloud the club uploads to.
"""
import os

CLOUD = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
LOGO_FOLDER = "baize/logos"


def cdn_logo_url(club_uid):
    if not CLOUD or not club_uid:
        return None
    return f"https://res.cloudinary.com/{CLOUD}/image/upload/{LOGO_FOLDER}/{club_uid}"