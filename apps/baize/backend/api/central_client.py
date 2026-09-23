"""Client for calling the central customer app (baize-customer) FROM the club.

The reverse of customer_api's bridge: the club signs each request with the
shared BRIDGE_SECRET and central verifies it. Customers live in central now, so
the club asks central to resolve players by phone / id and to record khata.
Every call fails soft (returns None) so the floor keeps working if central is
briefly unreachable.
"""
import hashlib
import hmac
import json as _json
import os
import time
import httpx


def _base():
    return os.environ.get('CENTRAL_URL', '').rstrip('/')


def _sign(method, path, body=b''):
    secret = os.environ.get('BRIDGE_SECRET', '')
    if not secret:
        return {}
    ts = str(int(time.time()))
    body_hash = hashlib.sha256(body or b'').hexdigest()
    msg = f"{ts}.{method.upper()}.{path}.{body_hash}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return {'X-Baize-Timestamp': ts, 'X-Baize-Signature': sig}


def _get(path, params=None):
    base = _base()
    if not base:
        return None
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(f"{base}{path}", params=params or {}, headers=_sign('GET', path))
        return r.json() if r.status_code == 200 else None
    except httpx.RequestError:
        return None


def _post(path, payload):
    base = _base()
    if not base:
        return None
    body = _json.dumps(payload).encode()
    headers = {**_sign('POST', path, body), 'Content-Type': 'application/json'}
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.post(f"{base}{path}", content=body, headers=headers)
        return r.json() if r.status_code in (200, 201) else None
    except httpx.RequestError:
        return None


# ── customer directory ──
def lookup_by_phone(phone):
    d = _get('/api/customer/directory/lookup', {'phone': phone})
    return d.get('customer') if d and d.get('found') else None


def get_customer(customer_id):
    if not customer_id:
        return None
    d = _get(f'/api/customer/directory/by-id/{customer_id}')
    return d.get('customer') if d and d.get('found') else None


# ── khata (customer tabs, owned by central) ──
def khata_charge(customer_id, club_uid, amount, description="", source="", ref=""):
    return _post('/api/customer/khata/charge', {
        "customerId": customer_id, "clubUid": club_uid, "amount": int(amount or 0),
        "description": description, "source": source, "ref": ref})


def khata_book(club_uid):
    d = _get('/api/customer/khata/book', {'clubUid': club_uid})
    return (d or {}).get('khata', []) if d else []


def khata_settle(customer_id, club_uid):
    return _post('/api/customer/khata/settle', {"customerId": customer_id, "clubUid": club_uid})


# ── game history (the customer's own copy of a session) ──
def push_game(payload):
    return _post('/api/customer/games', payload)