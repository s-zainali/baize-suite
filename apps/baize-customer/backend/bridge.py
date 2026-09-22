"""Signs service-to-service calls to club nodes so they can trust this app.

Mirrors the club's require_bridge verifier:
    signature = HMAC_SHA256(BRIDGE_SECRET, f"{ts}.{METHOD}.{path}.{sha256(body)}")
Sign the EXACT body bytes you send (see central.py — we serialize once and pass
`content=`, not `json=`, so the hash matches what the club reads)."""
import hashlib
import hmac
import time
import config


def sign(method: str, path: str, body: bytes = b"") -> dict:
    """Return the auth headers for a request. `path` must be the node path the
    club sees, e.g. '/api/customer/availability' (include any /<sync_id>)."""
    if not config.BRIDGE_SECRET:
        return {}   # warn-open on the club side; nothing to sign
    ts = str(int(time.time()))
    body_hash = hashlib.sha256(body or b"").hexdigest()
    msg = f"{ts}.{method.upper()}.{path}.{body_hash}".encode()
    sig = hmac.new(config.BRIDGE_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    return {"X-Baize-Timestamp": ts, "X-Baize-Signature": sig}