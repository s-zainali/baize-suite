"""
Sync Phase 3 — engine + push (local → cloud) with CHUNKED BATCHING.

Handles massive local seed data gracefully by chunking HTTP POST payloads,
preventing socket write timeouts and high-memory serialization spikes.
"""
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from models import (db, Branch, Lounge, PoolTable, PlaySession, SessionPlayer, Booking,
                    SessionSegment, ActivityLog, CanteenOrder, CanteenOrderItem,
                    Queue, Customer, GlobalRate, SyncCursor)
from dotenv import load_dotenv
load_dotenv()

SYNC_URL = os.environ.get('SYNC_URL', '').rstrip('/')

# Chunk size for pushing records over HTTP to avoid socket write timeouts
BATCH_SIZE = int(os.environ.get('SYNC_BATCH_SIZE', 500))

FK = lambda col, key, model, attr: (col, key, model, attr)

# Applied in THIS order (parents before children)
SYNC_SPEC = [
    ('customer',           Customer,        []),
    ('branch_ref',         None,            []),   # branches come from the licence server
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
PUSH_ENTITIES = [name for name, Model, _ in SYNC_SPEC if Model is not None]
PULL_ENTITIES = ['booking']

# In-memory sync health metrics
MAX_BACKOFF = 300  # 5 min backoff cap
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
    """One row → wire dict with integer FKs mapped to stable UIDs."""
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


def collect_changes_batch(entity, since, limit=BATCH_SIZE):
    """Local rows of `entity` changed since watermark, chunked by limit."""
    Model, fks = SPEC_BY_NAME[entity]
    q = Model.query
    if since is not None:
        q = q.filter(Model.updated_at > since)
    
    rows = q.order_by(Model.updated_at.asc()).limit(limit).all()
    serialized = [serialize(o, fks) for o in rows]
    # Keep track of the maximum updated_at timestamp in this batch
    max_updated = rows[-1].updated_at if rows else None
    return serialized, max_updated


def apply_rows(entity, rows):
    """Upsert incoming rows; keyed by sync_id, resolved stable FKs."""
    Model, fks = SPEC_BY_NAME[entity]
    fk_by_wire = {f[1]: f for f in fks}
    dt_cols = {c.key for c in Model.__table__.columns
               if getattr(c.type, 'python_type', None) is datetime}
    applied = 0

    for row in rows:
        fk_failed = False
        fk_resolved_values = {}

        for k, v in row.items():
            if k in fk_by_wire:
                local_col, _, Parent, attr = fk_by_wire[k]
                parent = Parent.query.filter_by(**{attr: v}).first() if v is not None else None
                col_obj = getattr(Model, local_col).property.columns[0]
                if not col_obj.nullable and parent is None and v is not None:
                    fk_failed = True
                    break
                fk_resolved_values[local_col] = parent.id if parent else None

        if fk_failed:
            continue

        obj = Model.query.filter_by(sync_id=row['sync_id']).first()
        incoming = _parse(row.get('updated_at'))
        if obj and obj.updated_at and incoming and incoming <= obj.updated_at:
            continue

        if obj is None:
            obj = Model(sync_id=row['sync_id'])
            db.session.add(obj)

        for k, v in row.items():
            if k in ('sync_id',):
                continue
            if k in fk_by_wire:
                local_col = fk_by_wire[k][0]
                setattr(obj, local_col, fk_resolved_values[local_col])
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
    """Iteratively pushes entity updates in BATCH_SIZE chunks, clearing failure flags immediately."""
    if not SYNC_URL:
        return {'pushed': 0, 'skipped': 'no SYNC_URL'}
    from license_util import active_sync_token
    token = active_sync_token()
    if not token:
        return {'pushed': 0, 'skipped': 'no token'}

    total_pushed = 0

    for entity in PUSH_ENTITIES:
        while True:
            cursor = _cursor(entity)
            since = cursor.last_pushed_at
            
            rows, max_updated = collect_changes_batch(entity, since, limit=BATCH_SIZE)
            if not rows:
                break

            payload = json.dumps({'entities': {entity: rows}}).encode()
            req = urllib.request.Request(
                f"{SYNC_URL}/api/sync/push",
                data=payload,
                method='POST',
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
            )

            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.loads(r.read().decode())

            # Advance cursor for this batch
            if max_updated:
                cursor.last_pushed_at = max_updated
                db.session.commit()

            total_pushed += len(rows)

            # --- KEY FIX FOR THE AMBER INDICATOR ---
            # As soon as a single HTTP request succeeds, mark health as OK so status.online becomes True.
            # With pending > 0, SyncIndicator.vue will render Amber ("Syncing").
            HEALTH['consecutive_failures'] = 0
            HEALTH['last_error'] = None
            HEALTH['last_ok_at'] = datetime.now()

            if len(rows) < BATCH_SIZE:
                break

    return {'pushed': total_pushed}

def pull_once():
    """Pulls cloud-authoritative records and updates local models."""
    if not SYNC_URL:
        return {'pulled': 0, 'skipped': 'no SYNC_URL'}
    from license_util import active_sync_token
    token = active_sync_token()
    since = min((c for c in (_cursor(e).last_pulled_at for e in PULL_ENTITIES) if c), default=None)
    qs = urllib.parse.urlencode({'entities': ','.join(PULL_ENTITIES),
                                 'since': since.isoformat() if since else ''})
    req = urllib.request.Request(f"{SYNC_URL}/api/sync/pull?{qs}", method='GET',
                                 headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=30) as r:
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


def pending_counts():
    """How many local records remain to be pushed."""
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
    """Status snapshot for the frontend UI health monitor."""
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


def start_sync_worker(app, interval=10):
    """Background loop pushing chunks in sequence."""
    from tenancy import IS_HYBRID
    if not (IS_HYBRID and SYNC_URL):
        return
    import threading, time as _t

    def _loop():
        delay = interval
        while True:
            _t.sleep(delay)
            try:
                with app.app_context():
                    res = push_once()
                    HEALTH['last_push_at'] = datetime.now()
                    pull_once()
                    HEALTH['last_pull_at'] = datetime.now()

                HEALTH.update(last_ok_at=datetime.now(), last_error=None, consecutive_failures=0)
                
                # If there are still items left in the queue, run immediately (2s delay) to drain fast
                delay = 2 if res.get('pushed', 0) > 0 else interval
            except Exception as e:
                HEALTH['consecutive_failures'] += 1
                HEALTH['last_error'] = str(e)[:200]
                delay = min(interval * (2 ** HEALTH['consecutive_failures']), MAX_BACKOFF)

    threading.Thread(target=_loop, daemon=True, name='baize-sync').start()
    """Background loop pushing chunks in sequence."""
    from tenancy import IS_HYBRID
    if not (IS_HYBRID and SYNC_URL):
        return
    import threading, time as _t

    def _loop():
        delay = interval
        while True:
            _t.sleep(delay)
            try:
                with app.app_context():
                    res = push_once()
                    HEALTH['last_push_at'] = datetime.now()
                    pull_once()
                    HEALTH['last_pull_at'] = datetime.now()

                HEALTH.update(last_ok_at=datetime.now(), last_error=None, consecutive_failures=0)
                
                # If we pushed a full batch, run immediately without sleeping long to drain the queue
                delay = 2 if res.get('pushed', 0) > 0 else interval
            except Exception as e:
                HEALTH['consecutive_failures'] += 1
                HEALTH['last_error'] = str(e)[:200]
                delay = min(interval * (2 ** HEALTH['consecutive_failures']), MAX_BACKOFF)

    threading.Thread(target=_loop, daemon=True, name='baize-sync').start()