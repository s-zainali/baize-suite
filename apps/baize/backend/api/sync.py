"""
Sync Phase 3 — engine + push (local → cloud).

The install pushes its local-authoritative operational data to the cloud so the
owner's Overview/analytics work over the internet. The install talks to the
cloud *API* (SYNC_URL), never the cloud DB directly.

The one hard problem: a row's foreign keys are LOCAL integer ids that mean
nothing in the cloud. So every relationship is serialized by its STABLE id
(branch_uid, a parent's sync_id, a lounge/table uid) and resolved back to a
local id on the receiving side. Rows are keyed by `sync_id`, upserted
last-write-wins by `updated_at`, and applied parent-first.
"""
import os
from datetime import datetime
from models import (db, Branch, Lounge, PoolTable, PlaySession, SessionPlayer, Booking,
                    SessionSegment, ActivityLog, CanteenOrder, CanteenOrderItem,
                    Queue, Customer, GlobalRate, SyncCursor)
from dotenv import load_dotenv
load_dotenv()

SYNC_URL = os.environ.get('SYNC_URL', '').rstrip('/')

# fk = (local_column, wire_key, ParentModel, parent_stable_attr)
#   parent_stable_attr is the STABLE id used across the boundary (uid / sync_id).
FK = lambda col, key, model, attr: (col, key, model, attr)

# Applied in THIS order (parents before children) so FK targets already exist.
SYNC_SPEC = [
    ('customer',           Customer,        []),
    ('branch_ref',         None,            []),   # branches come from the licence server; not pushed
    ('lounge',             Lounge,          [FK('branch_id', 'branch_uid', Branch, 'uid')]),
    ('global_rate',        GlobalRate,      [FK('branch_id', 'branch_uid', Branch, 'uid')]),
    ('play_session',       PlaySession,     [FK('branch_id', 'branch_uid', Branch, 'uid'),
                                             FK('customer_id', 'customer_sid', Customer, 'sync_id')]),
    ('pool_table',         PoolTable,       [FK('branch_id', 'branch_uid', Branch, 'uid'),
                                             FK('session_id', 'session_sid', PlaySession, 'sync_id')]),
    ('session_player',     SessionPlayer,   [FK('session_id', 'session_sid', PlaySession, 'sync_id'),
                                             FK('customer_id', 'customer_sid', Customer, 'sync_id')]),
    ('session_segment',    SessionSegment,  [FK('session_id', 'session_sid', PlaySession, 'sync_id')]),
    ('activity_log',       ActivityLog,     [FK('branch_id', 'branch_uid', Branch, 'uid'),
                                             FK('session_id', 'session_sid', PlaySession, 'sync_id'),
                                             FK('customer_id', 'customer_sid', Customer, 'sync_id')]),
    ('canteen_order',      CanteenOrder,    [FK('branch_id', 'branch_uid', Branch, 'uid'),
                                             FK('session_id', 'session_sid', PlaySession, 'sync_id')]),
    ('canteen_order_item', CanteenOrderItem,[FK('order_id', 'order_sid', CanteenOrder, 'sync_id')]),
    ('queue',              Queue,           [FK('branch_id', 'branch_uid', Branch, 'uid')]),
    ('booking',            Booking,         [FK('branch_id', 'branch_uid', Branch, 'uid'),
                                             FK('customer_id', 'customer_sid', Customer, 'sync_id')]),
]
SPEC_BY_NAME = {name: (Model, fks) for name, Model, fks in SYNC_SPEC if Model is not None}
# entities the LOCAL install owns and pushes up
PUSH_ENTITIES = [name for name, Model, _ in SYNC_SPEC if Model is not None]
# cloud-authoritative entities the install PULLS down (online bookings). A
# walk-in booking the install pushed up comes back here but is idempotently
# skipped (its updated_at isn't newer), so there's no ping-pong.
PULL_ENTITIES = ['booking']

# ── sync health (in-memory; reset on process restart) ──
MAX_BACKOFF = 300  # seconds — cap the retry delay when the cloud is unreachable
HEALTH = {'last_ok_at': None, 'last_push_at': None, 'last_pull_at': None,
          'last_error': None, 'consecutive_failures': 0}


def _iso(dt):
    return dt.isoformat() if isinstance(dt, datetime) else None


def _parse(v):
    if not v:
        return None
    try:
        return datetime.fromisoformat(v)
    except (ValueError, TypeError):
        return None


def serialize(obj, fks):
    """One row → a wire dict: scalar columns as-is, integer FKs replaced by the
    parent's stable id."""
    fk_cols = {f[0] for f in fks}
    out = {'sync_id': obj.sync_id, 'updated_at': _iso(obj.updated_at),
           'deleted_at': _iso(getattr(obj, 'deleted_at', None))}
    for col in obj.__table__.columns:
        n = col.key
        if n in ('id', 'sync_id', 'updated_at', 'deleted_at') or n in fk_cols:
            continue
        v = getattr(obj, n)
        out[n] = _iso(v) if isinstance(v, datetime) else v
    for local_col, wire_key, Parent, attr in fks:
        pid = getattr(obj, local_col)
        parent = db.session.get(Parent, pid) if pid is not None else None
        out[wire_key] = getattr(parent, attr) if parent else None
    return out


def collect_changes(entity, since):
    """Local rows of `entity` changed since the watermark, serialized."""
    Model, fks = SPEC_BY_NAME[entity]
    q = Model.query
    if since is not None:
        q = q.filter(Model.updated_at > since)
    return [serialize(o, fks) for o in q.order_by(Model.updated_at.asc()).all()]


def apply_rows(entity, rows):
    """Upsert incoming rows into THIS database (the cloud side on push). Keyed by
    sync_id; last-write-wins by updated_at; FK stable ids resolved to local ids."""
    Model, fks = SPEC_BY_NAME[entity]
    fk_by_wire = {f[1]: f for f in fks}
    # datetime columns arrive as ISO strings and must be parsed back, or the DB
    # driver rejects them (only updated_at/deleted_at were handled before).
    dt_cols = {c.key for c in Model.__table__.columns
               if getattr(c.type, 'python_type', None) is datetime}
    applied = 0
    for row in rows:
        obj = Model.query.filter_by(sync_id=row['sync_id']).first()
        incoming = _parse(row.get('updated_at'))
        if obj and obj.updated_at and incoming and incoming <= obj.updated_at:
            continue                                   # stale — keep ours
        if obj is None:
            obj = Model(sync_id=row['sync_id'])
            db.session.add(obj)
        for k, v in row.items():
            if k in ('sync_id',):
                continue
            if k in fk_by_wire:
                local_col, _, Parent, attr = fk_by_wire[k]
                parent = Parent.query.filter_by(**{attr: v}).first() if v is not None else None
                setattr(obj, local_col, parent.id if parent else None)
            elif k in dt_cols:
                setattr(obj, k, _parse(v) if isinstance(v, str) else v)
            elif hasattr(obj, k):
                setattr(obj, k, v)
        applied += 1
    db.session.commit()
    return applied


def _cursor(entity):
    c = db.session.get(SyncCursor, entity)
    if c is None:
        c = SyncCursor(entity=entity)
        db.session.add(c)
        db.session.commit()
    return c


def push_once():
    """Collect everything changed since each entity's push cursor and POST it to
    the cloud. Advances cursors on the SERVER clock it returns (avoids skew)."""
    if not SYNC_URL:
        return {'pushed': 0, 'skipped': 'no SYNC_URL'}
    import json, urllib.request
    from license_util import active_license
    lic = active_license()
    token = lic.token if lic else None
    payload = {}
    for entity in PUSH_ENTITIES:
        since = _cursor(entity).last_pushed_at
        rows = collect_changes(entity, since)
        if rows:
            payload[entity] = rows
    if not payload:
        return {'pushed': 0}
    body = json.dumps({'entities': payload}).encode()
    req = urllib.request.Request(f"{SYNC_URL}/api/sync/push", data=body, method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = json.loads(r.read().decode())
    server_now = _parse(resp.get('serverTime')) or datetime.now()
    for entity in payload:
        _cursor(entity).last_pushed_at = server_now
    db.session.commit()
    return {'pushed': sum(len(v) for v in payload.values())}


def pull_once():
    """Pull cloud-authoritative changes (online bookings) since our pull cursor
    and apply them locally, FK-remapping stable ids to local ids. Advances
    cursors on the SERVER clock it returns."""
    if not SYNC_URL:
        return {'pulled': 0, 'skipped': 'no SYNC_URL'}
    import json, urllib.request, urllib.parse
    from license_util import active_license
    lic = active_license()
    token = lic.token if lic else None
    since = min((c for c in (_cursor(e).last_pulled_at for e in PULL_ENTITIES) if c), default=None)
    qs = urllib.parse.urlencode({'entities': ','.join(PULL_ENTITIES),
                                 'since': since.isoformat() if since else ''})
    req = urllib.request.Request(f"{SYNC_URL}/api/sync/pull?{qs}", method='GET',
                                 headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = json.loads(r.read().decode())
    entities = resp.get('entities', {})
    applied = 0
    for name in PULL_ENTITIES:
        rows = entities.get(name)
        if rows:
            applied += apply_rows(name, rows)
    server_now = _parse(resp.get('serverTime')) or datetime.now()
    for e in PULL_ENTITIES:
        _cursor(e).last_pulled_at = server_now
    db.session.commit()
    return {'pulled': applied}


def collect_pull(entities, since):
    """Cloud side of /sync/pull: serialize each requested entity's rows changed
    since the cursor, for the tenant already pinned by the request."""
    out = {}
    for name in entities:
        if name in PULL_ENTITIES and name in SPEC_BY_NAME:
            rows = collect_changes(name, since)
            if rows:
                out[name] = rows
    return out


def apply_push(payload):
    """Apply a pushed batch (cloud side). Parents first (SYNC_SPEC order) so FK
    targets exist when children resolve them."""
    entities = payload.get('entities', {})
    total = 0
    for name in PUSH_ENTITIES:
        rows = entities.get(name)
        if rows:
            total += apply_rows(name, rows)
    return total


def pending_counts():
    """How many local rows are waiting to push, per entity — drives the UI badge."""
    out = {}
    for entity in PUSH_ENTITIES:
        Model = SPEC_BY_NAME[entity][0]
        since = _cursor(entity).last_pushed_at
        q = Model.query
        if since is not None:
            q = q.filter(Model.updated_at > since)
        n = q.count()
        if n:
            out[entity] = n
    return out


def sync_status():
    """A snapshot for the sync-health indicator: mode, last success, backlog, error."""
    from tenancy import IS_HYBRID, IS_CLOUD
    mode = 'cloud' if IS_CLOUD else ('hybrid' if IS_HYBRID else 'local')
    active = bool(IS_HYBRID and SYNC_URL)
    st = {
        'mode': mode,
        'syncing': active,
        'online': HEALTH['consecutive_failures'] == 0 and HEALTH['last_ok_at'] is not None,
        'lastError': HEALTH['last_error'],
        'consecutiveFailures': HEALTH['consecutive_failures'],
        'lastOkAt': HEALTH['last_ok_at'].isoformat() if HEALTH['last_ok_at'] else None,
        'lastPushAt': HEALTH['last_push_at'].isoformat() if HEALTH['last_push_at'] else None,
        'lastPullAt': HEALTH['last_pull_at'].isoformat() if HEALTH['last_pull_at'] else None,
        'pending': {},
    }
    if active:
        try:
            st['pending'] = pending_counts()
        except Exception:
            pass
    return st


def start_sync_worker(app, interval=30):
    """Background push loop for a hybrid (local+cloud) install. No-op without
    SYNC_URL. Pushes local changes to the cloud every `interval` seconds."""
    from tenancy import IS_HYBRID
    if not (IS_HYBRID and SYNC_URL):
        return                       # only a hybrid install pushes up to the cloud
    import threading, time as _t

    def _loop():
        delay = interval
        while True:
            _t.sleep(delay)
            try:
                with app.app_context():
                    push_once();  HEALTH['last_push_at'] = datetime.now()
                    pull_once();  HEALTH['last_pull_at'] = datetime.now()
                HEALTH.update(last_ok_at=datetime.now(), last_error=None, consecutive_failures=0)
                delay = interval                              # recovered — back to normal cadence
            except Exception as e:
                HEALTH['consecutive_failures'] += 1
                HEALTH['last_error'] = str(e)[:200]
                # exponential backoff so an offline spell doesn't hammer the network
                delay = min(interval * (2 ** HEALTH['consecutive_failures']), MAX_BACKOFF)

    threading.Thread(target=_loop, daemon=True, name='baize-sync').start()