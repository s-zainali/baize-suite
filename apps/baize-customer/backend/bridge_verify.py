"""Verify service calls FROM a club node (the reverse of the club's require_bridge).

Same HMAC-over-shared-secret scheme, so the club signs with BRIDGE_SECRET and we
verify here. Used to guard the customer directory + khata endpoints the club
calls. Warn-open in dev when unset; fail-closed in production.
"""
import hashlib
import hmac
import time
from fastapi import Request, HTTPException
import config


async def require_bridge(request: Request):
    if not config.BRIDGE_SECRET:
        if config.IS_PROD:
            raise HTTPException(503, "service auth not configured")
        return  # dev warn-open
    ts = request.headers.get("X-Baize-Timestamp", "")
    sig = request.headers.get("X-Baize-Signature", "")
    if not ts or not sig:
        raise HTTPException(401, "unauthorized")
    try:
        if abs(time.time() - int(ts)) > 300:
            raise HTTPException(401, "stale request")
    except ValueError:
        raise HTTPException(401, "unauthorized")
    body = await request.body()
    body_hash = hashlib.sha256(body or b"").hexdigest()
    msg = f"{ts}.{request.method.upper()}.{request.url.path}.{body_hash}".encode()
    expected = hmac.new(config.BRIDGE_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(401, "unauthorized")