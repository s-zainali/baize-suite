import os
import sys
import json
import math
import random
import secrets
import time
import hmac
import hashlib
import httpx
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from waitress import serve
from datetime import datetime, timezone, timedelta
from sqlalchemy import inspect as sa_inspect, text as sa_text, func
from models import *
from flask import abort
from flask_jwt_extended import (
    JWTManager, create_access_token, verify_jwt_in_request, get_jwt
)
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()


# --- SETUP PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))       
DIST_DIR = os.path.join(os.path.dirname(BASE_DIR), 'dist') 
BACKEND_DIR = os.path.dirname(BASE_DIR) 
DEFAULT_RATES = {
    'snooker':        {'weekday': 8,  'weekend': 10},
    'pool':           {'weekday': 6,  'weekend': 8},
    'privatePool':    {'weekday': 8,  'weekend': 10},
    'privateSnooker': {'weekday': 10, 'weekend': 13},
    'ps5':            {'weekday': 15, 'weekend': 20},
    'foosball':       {'weekday': 5,  'weekend': 7},
}

app = Flask(__name__, 
            static_folder=os.path.join(DIST_DIR, 'assets'), 
            template_folder=DIST_DIR)
CORS(app)


@app.errorhandler(Exception)
def report_unhandled(error):
    """Return failures as JSON, with CORS headers attached.

    Flask's default 500 page is HTML and skips the after-request hook that adds
    CORS headers, so a server error reaching a browser on another origin shows
    up as "CORS header missing" — which sends you looking for a CORS problem
    that isn't there. This keeps the real error visible.
    """
    from werkzeug.exceptions import HTTPException

    if isinstance(error, HTTPException):
        response = jsonify({'error': error.description})
        response.status_code = error.code
    else:
        app.logger.exception('Unhandled error on %s', request.path)
        response = jsonify({
            'error': 'Server error',
            'detail': f'{type(error).__name__}: {error}',
            'path': request.path,
        })
        response.status_code = 500

    origin = request.headers.get('Origin')
    if origin:
        response.headers.setdefault('Access-Control-Allow-Origin', origin)
        response.headers.setdefault('Vary', 'Origin')
    return response

db_url = (os.environ.get('DATABASE_URL') or '').strip()
if not db_url:
    # Fail loudly rather than silently opening a stray local database file.
    raise RuntimeError(
        'DATABASE_URL is not set. This app runs on Postgres.\n'
        '  Local:  DATABASE_URL=postgresql://baize:baize@localhost:5432/lounge '
        '(docker compose sets this for you)'
    )
# Some hosts hand back the legacy postgres:// scheme; SQLAlchemy needs postgresql://
app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecret'  # Secret key for session management and JWT
app.config['SECURITY_PASSWORD_SALT'] = 'salt'  # Salt for hashing passwords
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'SECRETKEYFORENCRYPTION')
# Staff tokens are stamped and checked with aud="staff". A customer token is
# signed with a different key entirely (see customer_api.py), so it fails
# signature verification here before the audience is even considered — the two
# token families cannot be interchanged in either direction.
app.config['JWT_ENCODE_AUDIENCE'] = 'staff'
app.config['JWT_DECODE_AUDIENCE'] = 'staff'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=12)

jwt = JWTManager(app)

db.init_app(app)
from tenancy import install_tenancy, enable_rls, IS_CLOUD
install_tenancy(app, db)   # pins each request to its club (cloud/hybrid); inert locally
from sync import start_sync_worker
start_sync_worker(app)     # hybrid install: background push to the cloud (no-op without SYNC_URL)

# Alembic, via Flask-Migrate, owns the schema now. `flask db upgrade` applies
# migrations the same in every environment, so the schema is written once
# and can't drift between local and production the way the old hand-rolled
# per-dialect DDL did. The directory is pinned to an absolute path so the
# migration commands resolve the same whether they're run from the repo root
# (Render) or from backend/ (the container entrypoint and local dev).
migrate = Migrate(app, db, directory=os.path.join(BACKEND_DIR, 'migrations'))

ROLE_LEVEL = {'receptionist': 1, 'manager': 2, 'owner': 3}

# The areas a person can work. A receptionist is granted these individually on
# their account; managers and owners cover everything, so their access is
# derived rather than stored — one source of truth, nothing to drift.
CAPABILITIES = ('floor', 'canteen')
FULL_ACCESS_ROLES = ('manager', 'owner')


def parse_capabilities(raw):
    """Normalise a stored or submitted capability list, dropping anything unknown."""
    items = raw if isinstance(raw, (list, tuple, set)) else str(raw or '').split(',')
    wanted = {str(i).strip().lower() for i in items}
    return [c for c in CAPABILITIES if c in wanted]


def capabilities_for(user):
    """What this user may work on."""
    if user.role in FULL_ACCESS_ROLES:
        return list(CAPABILITIES)
    # Never leave an account with no counter at all — it could sign in and
    # then find every page closed to it.
    return parse_capabilities(user.capabilities) or ['floor']


def current_role():
    verify_jwt_in_request()
    return (get_jwt() or {}).get('role')


def current_capabilities():
    verify_jwt_in_request()
    claims = get_jwt() or {}
    if claims.get('role') in FULL_ACCESS_ROLES:
        return list(CAPABILITIES)
    return parse_capabilities(claims.get('capabilities'))


def require_role(min_role):
    """Call at the top of a route: aborts 401 if no valid token, 403 if role too low."""
    verify_jwt_in_request()
    claims = get_jwt()
    if ROLE_LEVEL.get(claims.get('role'), 0) < ROLE_LEVEL[min_role]:
        abort(403)


def require_capability(*capabilities):
    """Area gate: the user must be able to work at least one of these counters."""
    if not set(current_capabilities()).intersection(capabilities):
        abort(403)


def require_canteen_admin():
    """Managing the menu belongs to whoever runs the canteen."""
    require_capability('canteen')


# ── Branch scoping (multi-branch, Phase 2) ───────────────────────────────────
# Every request resolves to a set of branches the user may touch. Reads are
# filtered to that set; writes are stamped with the selected branch. With a
# single (default) branch this is a no-op — everyone is allowed everywhere — so
# it changes nothing until real branches + assignments exist (Phase 3).
def _default_branch_id():
    b = (Branch.query.filter_by(is_default=True, deleted_at=None).first()
         or Branch.query.filter_by(deleted_at=None).order_by(Branch.id).first())
    return b.id if b else None


def _current_user_obj():
    sub = _safe_claims().get('sub')
    try:
        return User.query.get(int(sub)) if sub else None
    except Exception:                            # noqa: BLE001
        return None


def _safe_claims():
    """JWT claims for the CURRENT request, verifying the token optionally first.
    Safe to call in before_request (before route auth) — returns {} when there's
    no/invalid token instead of raising."""
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt() or {}
    except Exception:
        return {}


def _licensed_branch_ids():
    """Branch ids actually permitted to OPERATE: the default branch (authorised
    by the club licence) plus any branch backed by a valid, server-issued branch
    licence. A branch row pushed straight into the DB has no branch licence, so
    it isn't here and cannot operate — closing the direct-insert bypass. Each
    branch is registered on the licence server; there is no simple count."""
    from license_util import active_branch_license, _branch_valid
    ok = set()
    for b in Branch.query.filter_by(deleted_at=None).all():
        bl = active_branch_license(b.uid)
        if bl and _branch_valid(bl):             # every branch needs its own server-issued licence
            ok.add(b.id)                         # (no default exception — the auto "Main Branch" no longer operates)
    return ok


def allowed_branch_ids():
    """Branch ids the current user may access — intersected with the branches
    that are actually licensed to operate (see _licensed_branch_ids). Owner →
    every licensed branch; manager/staff → their assigned licensed branches,
    falling back to the default."""
    licensed = _licensed_branch_ids()
    claims = _safe_claims()
    
    # 1. Authenticated Owner: Full access to all licensed branches
    if claims.get('role') == 'owner':
        return [b.id for b in Branch.query.filter_by(deleted_at=None).order_by(Branch.sort_order, Branch.id).all()
                if b.id in licensed]
    
    # 2. Authenticated Staff: Restricted strictly to assigned branches
    u = _current_user_obj()
    if u:
        ids = [b.id for b in u.branches if b.deleted_at is None and b.id in licensed]
        if ids:
            return ids
        d = _default_branch_id()
        return [d] if (d is not None and d in licensed) else []

    # 3. Unauthenticated / Public API Requests (e.g., public /api/table-types):
    # Allow looking up options across any active licensed branch
    return list(licensed)


def selected_branch_id():
    """The single branch this request writes to / focuses on: the X-Branch header
    when the user may access it, else their primary branch, else the first allowed."""
    allowed = allowed_branch_ids()
    hdr = request.headers.get('X-Branch')
    
    # Must be in ALLOWED (enforces user permissions for staff, permits licensed for public)
    if hdr and hdr.isdigit() and int(hdr) in allowed:
        return int(hdr)
        
    u = _current_user_obj()
    if u and u.primary_branch_id in allowed:
        return u.primary_branch_id
        
    return allowed[0] if allowed else None


def _type_entitled(table_type, branch_id=None):
    """A station type is usable only if it's a base (pool) renderer or its
    module is licensed. Enforced on live actions so a station created while a
    feature was licensed stops working once that feature is dropped."""
    tt = TableType.query.filter_by(key=table_type).first()
    if tt is None:
        return False                     # unknown type → default-deny
    feats = _features_for_branch(branch_id if branch_id is not None else selected_branch_id())
    return tt.renderer == 'pool' or tt.renderer in feats


def _assign_branches(user, branch_ids, primary_id):
    """Attach a user to branches. Owners implicitly see all (rows optional);
    employees are single-branch; managers may hold several. Falls back to the
    default branch so no user is left unattached."""
    valid = {b.id: b for b in Branch.query.filter_by(deleted_at=None).all()}
    ids = [i for i in (branch_ids or []) if i in valid]
    if user.role not in ('manager', 'owner') and len(ids) > 1:
        ids = ids[:1]                              # employees are single-branch
    if not ids:
        d = _default_branch_id()
        ids = [d] if d is not None else []
    user.branches = [valid[i] for i in ids]
    user.primary_branch_id = primary_id if primary_id in ids else (ids[0] if ids else None)


def _features_for_branch(branch_id):
    """Add-on modules available AT a branch: its OWN branch licence if it has
    one, else the club's main licence (backward-compatible for the default
    branch and installs from before per-branch licensing)."""
    from license_util import branch_features, active_branch_license
    b = Branch.query.get(branch_id) if branch_id is not None else None
    if b and active_branch_license(b.uid):
        return branch_features(b.uid)
    return set()          # no branch licence → base (pool) only; there is no club licence


def _selected_features():
    return _features_for_branch(selected_branch_id())


def _branch_scope(Model):
    """Operational (floor) scope: rows for the ONE branch the request is working
    (the selected branch), so a receptionist at branch A never sees branch B's
    floor. Legacy NULL-branch rows stay visible during rollout."""
    sel = selected_branch_id()
    return (Model.branch_id == sel) | Model.branch_id.is_(None)


def _branch_report_scope(Model):
    """Reconciliation / analytics scope: a specific branch when one is selected
    via X-Branch, otherwise every branch the user may see (combined). This is
    what powers per-branch AND combined reconciliation."""
    allowed = allowed_branch_ids()
    hdr = request.headers.get('X-Branch')
    if hdr and hdr.isdigit() and int(hdr) in allowed:
        return (Model.branch_id == int(hdr)) | Model.branch_id.is_(None)
    return Model.branch_id.in_(allowed) | Model.branch_id.is_(None)

# flask_jwt_extended answers an unverifiable token with 422 by default. A
# customer token presented to a staff route IS rejected either way, but 422
# reads as "malformed request" and the frontend's authFetch only clears the
# session on 401 — so a stale or foreign token would leave the user stuck
# instead of being signed out. Every auth failure is a 401 here.
@jwt.invalid_token_loader
def _invalid_token(reason):
    return jsonify({'error': 'Not authorised'}), 401


@jwt.unauthorized_loader
def _missing_token(reason):
    return jsonify({'error': 'Not authorised'}), 401


@jwt.expired_token_loader
def _expired_token(header, payload):
    return jsonify({'error': 'Session expired'}), 401


@jwt.revoked_token_loader
def _revoked_token(header, payload):
    return jsonify({'error': 'Session expired'}), 401


# --- DEPLOYMENT ROLE ---
#
#   all      both surfaces in one process (single club, today)
#   staff    club machine on the LAN, no public signup
#   customer public portal only, no till or revenue routes registered
#
# Splitting later is a config change, not a rewrite — which only holds because
# the customer code is a self-contained blueprint.
APP_ROLE = os.environ.get('APP_ROLE', 'all').lower()
SERVE_STAFF = APP_ROLE in ('all', 'staff')
SERVE_CUSTOMER = APP_ROLE in ('all', 'customer')

if SERVE_CUSTOMER:
    import customer_api
    from customer_api import customer_bp
    app.register_blueprint(customer_bp)

if SERVE_STAFF:
    from canteen_api import register_canteen_routes, seed_canteen

    def _current_username():
        """Whoever is holding the till, for the order's audit trail."""
        try:
            # `sub` is the user id — reading that recorded a number in every
            # 'served by' and 'closed by' field. The username is its own claim.
            claims = get_jwt() or {}
            return claims.get('username') or ''
        except Exception:                       # noqa: BLE001 - no request context
            return ''


@app.before_request
def enforce_deployment_role():
    """Hard gate on the whole staff surface when this process is customer-only.

    The staff routes are defined at module scope, so they always exist as Flask
    rules. This makes them unreachable rather than merely unauthorised.
    """
    path = request.path
    if not SERVE_STAFF and path.startswith('/api/') and not path.startswith('/api/customer'):
        return jsonify({'error': 'Not found'}), 404
    if not SERVE_CUSTOMER and path.startswith('/api/customer'):
        return jsonify({'error': 'Not found'}), 404
    return None


# --- SESSION / BILLING ENGINE ---
#
# A tab (PlaySession) is made of one or more segments. A segment is a stretch of
# play on a single station at a single rate. Segments close and reopen on every
# transfer and on every stop/resume, which is what lets a tab that moved from a
# pool table to a snooker table bill each stretch at its own rate.

UTC_NOW = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC, matches storage


def rate_for(table_type, when=None):
    """Rate in force right now for a table type (weekend = Sat/Sun, local time)."""
    row = GlobalRate.query.filter_by(table_type=table_type).first()
    if not row:
        return 0
    when = when or datetime.now()
    return row.weekend_rate if when.weekday() >= 5 else row.weekday_rate


def lounge_name_for(table):
    if not table.lounge_uid:
        return ''
    lounge = Lounge.query.filter_by(uid = table.lounge_uid).first()
    return lounge.name if lounge else ''


def open_segment(session, table, when=None):
    when = when or UTC_NOW()
    segment = SessionSegment(
        session_id=session.id,
        table_uid=table.uid,
        table_type=table.table_type,
        table_number=table.table_id,
        lounge_name=lounge_name_for(table),
        rate=rate_for(table.table_type),
        start_time=when,
    )
    db.session.add(segment)
    return segment


def close_open_segments(session, when=None):
    when = when or UTC_NOW()
    for segment in SessionSegment.query.filter_by(session_id=session.id, end_time=None).all():
        segment.end_time = when


def prior_seconds(session_id):
    """Seconds already banked on closed segments of this tab."""
    if not session_id:
        return 0
    total = 0
    for segment in SessionSegment.query.filter_by(session_id=session_id).all():
        if segment.end_time:
            total += max(0, int((segment.end_time - segment.start_time).total_seconds()))
    return total


def pending_total(session_id):
    """What an open tab would cost if it were settled right now."""
    if not session_id:
        return 0
    session = PlaySession.query.get(session_id)
    return build_invoice(session)['totalCost'] if session else 0


def ensure_session(table):
    """Attach a tab to a station that is running without one.

    Only relevant for sessions that were already in flight when this version was
    deployed — they keep their original start time and bill normally.
    """
    if table.session_id:
        return PlaySession.query.get(table.session_id)
    if not table.is_active:
        return None
    session = PlaySession(
        guest_name=table.booking_name or '',
        status='active',
        receipt_id=random.randint(100000, 999999),
        branch_id=table.branch_id,
    )
    db.session.add(session)
    db.session.flush()
    table.session_id = session.id
    open_segment(session, table, table.start_time or UTC_NOW())
    return session


def format_elapsed(seconds):
    hours, minutes, secs = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    if hours > 0:
        return f'{hours}:{minutes:02d}:{secs:02d}'
    return f'{minutes:02d}:{secs:02d}'


def build_invoice(session):
    """Price a tab segment by segment.

    Whole billable minutes are allocated across segments by largest remainder, so
    the per-station minutes always add up to ceil(total_time) rather than each
    segment rounding up independently. Two minutes of pool followed by forty of
    snooker bills as 2 + 40, not 3 + 41.
    """
    now = UTC_NOW()
    segments = (SessionSegment.query
                .filter_by(session_id=session.id)
                .order_by(SessionSegment.id)
                .all())

    rows = []
    for segment in segments:
        end = segment.end_time or now
        rows.append({
            'tableUid': segment.table_uid,
            'tableType': segment.table_type,
            'tableId': segment.table_number,
            'lounge': segment.lounge_name or '',
            'rate': segment.rate,
            'seconds': max(0, int((end - segment.start_time).total_seconds())),
            'running': segment.end_time is None,
        })

    total_seconds = sum(r['seconds'] for r in rows)
    total_minutes = math.ceil(total_seconds / 60) if total_seconds else 0

    minutes = [r['seconds'] // 60 for r in rows]
    shortfall = total_minutes - sum(minutes)
    if shortfall > 0 and rows:
        # Hand the leftover minutes to the segments with the biggest part-minutes
        order = sorted(range(len(rows)), key=lambda i: (-(rows[i]['seconds'] % 60), -rows[i]['seconds']))
        for k in range(shortfall):
            minutes[order[k % len(order)]] += 1

    for row, mins in zip(rows, minutes):
        row['billableMins'] = mins
        row['cost'] = mins * row['rate']
        row['elapsed'] = format_elapsed(row['seconds'])

    play_total = sum(r['cost'] for r in rows)

    # Canteen orders put on this tab are billed with the session rather than
    # taken at the counter, so they belong on this receipt.
    canteen_orders = (CanteenOrder.query
                      .filter_by(session_id=session.id, status='paid', payment_method='tab')
                      .order_by(CanteenOrder.id)
                      .all())
    canteen_lines = []
    for order in canteen_orders:
        for item in CanteenOrderItem.query.filter_by(order_id=order.id).all():
            canteen_lines.append({
                'name': item.name, 'qty': item.qty,
                'price': item.unit_price, 'cost': item.line_total,
            })
        if order.discount_amount:
            canteen_lines.append({
                'name': f'Discount ({order.discount_percent}%)', 'qty': 1,
                'price': -order.discount_amount, 'cost': -order.discount_amount,
            })
    # Order totals, not line totals — the orders carry their own discounts.
    canteen_total = sum(order.total for order in canteen_orders)

    total_cost = play_total + canteen_total
    last = rows[-1] if rows else {}
    # Headline rate for the ledger column: whichever station carried the most time
    headline = max(rows, key=lambda r: r['billableMins'], default=None)

    return {
        'receiptId': session.receipt_id,
        'sessionId': session.id,
        # A khata needs somebody to chase, so it's offered only when the tab
        # carries a name. A nameless walk-in must settle at the counter.
        'player': session.guest_name or 'Walk-in Guest',
        'isWalkIn': not (session.guest_name or '').strip(),
        'customerId': session.customer_id,
        'date': datetime.now().strftime('%-m/%-d/%Y, %-I:%M:%S %p'),
        'lounge': last.get('lounge', ''),
        'tableType': last.get('tableType', ''),
        'tableId': last.get('tableId', 0),
        'elapsed': format_elapsed(total_seconds),
        'billableMins': total_minutes,
        'servedBy' : _current_username(),
        'rate': headline['rate'] if headline else 0,
        'playTotal': play_total,
        'canteenTotal': canteen_total,
        'canteenItems': canteen_lines,
        'totalCost': total_cost,
        'segments': rows,
    }


def parse_segments(raw):
    """Read a JSON column back into a list, tolerating null or corrupt values.

    Every caller wants a list it can iterate; returning None here would make a
    reopened bill throw rather than simply show no line items.
    """
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return []
    return value if isinstance(value, list) else []


def upsert_log(invoice, session):
    """One ledger row per tab, updated in place when a tab is resumed and re-stopped."""
    log = ActivityLog.query.filter_by(session_id=session.id).first()
    if not log:
        log = ActivityLog(session_id=session.id, branch_id=getattr(session, 'branch_id', None) or selected_branch_id())
        db.session.add(log)
    log.receipt_id = invoice['receiptId']
    log.date_string = invoice['date']
    log.lounge = invoice['lounge']
    log.table_type = invoice['tableType']
    log.table_id = invoice['tableId'] or 0
    log.player = invoice['player']
    log.elapsed = invoice['elapsed']
    log.billable_mins = invoice['billableMins']
    log.rate = invoice['rate']
    # Table revenue only. The canteen orders on this tab keep their own rows,
    # so canteen sales are never reported as table sales.
    log.total_cost = invoice.get('playTotal', invoice['totalCost'])
    log.segments_json = json.dumps(invoice['segments'])
    log.canteen_json = json.dumps(invoice.get('canteenItems') or [])
    log.play_total = invoice.get('playTotal')
    log.canteen_total = invoice.get('canteenTotal')
    if not log.created_at:
        log.created_at = datetime.now()
    # Booking-started tabs carry the customer on the session even when the
    # invoice doesn't name them — fall back to it so history/analytics link up.
    log.customer_id = invoice.get('customerId') or session.customer_id
    db.session.flush()
    invoice['logId'] = log.id
    invoice['paymentStatus'] = log.payment_status
    return log


MAX_PLAYERS = 8


def normalise_players(players, booking_name=None):
    """Clean a submitted roster into [{name, customerId}].

    A walk-in name is split on commas: "Ali, Sara" is two people, not one guest
    called "Ali, Sara". Comma is how this app has always joined a roster, so a
    comma inside a typed name means two players — and every path that starts a
    table (the card's picker, a queue entry, a booking) gets the same treatment,
    so walk-ins are registered separately no matter where the name came from.

    A LINKED account is never split: it is one real person with one real name,
    and a comma in it (unlikely as that is) is part of that name.

    Accepts the old single-name form too, so a client that hasn't been updated
    still starts a session rather than none.
    """
    cleaned = []
    seen = set()

    def add(name, customer_id):
        name = str(name or '').strip()[:100]
        if not name:
            return
        # Same person added twice — by name, or by linking an account already
        # on the list.
        key = customer_id if customer_id else name.lower()
        if key in seen:
            return
        seen.add(key)
        cleaned.append({'name': name, 'customerId': customer_id})

    def add_walkins(raw):
        # A typed name may carry several walk-ins separated by commas.
        for part in str(raw or '').split(','):
            if len(cleaned) >= MAX_PLAYERS:
                break
            add(part, None)

    for entry in (players or []):
        if len(cleaned) >= MAX_PLAYERS:
            break
        if isinstance(entry, str):
            add_walkins(entry)
            continue
        customer_id = entry.get('customerId') or entry.get('customer_id')
        if customer_id:
            add(entry.get('name', ''), customer_id)   # a real account — never split
        else:
            add_walkins(entry.get('name', ''))

    if not cleaned and (booking_name or '').strip():
        add_walkins(booking_name)

    return cleaned


def players_for(session_id):
    """The roster on a session, for display."""
    if not session_id:
        return []
    rows = SessionPlayer.query.filter_by(session_id=session_id).order_by(SessionPlayer.id).all()
    return [{
        'name': r.name,
        'customerId': r.customer_id,
        'linked': r.customer_id is not None,
    } for r in rows]


def start_session(table, booking_name, players=None):
    # A lingering stopped tab on this station is settled rather than resumed
    if table.session_id:
        previous = PlaySession.query.get(table.session_id)
        if previous and previous.status != 'settled':
            previous.status = 'settled'
    # ...and so is any booking that was still riding it, or the old guest's
    # reservation would stay 'In progress' and block the table indefinitely.
    release_table_bookings(table)

    roster = normalise_players(players, booking_name)

    session = PlaySession(
        # The joined names stay the session's display label, so every existing
        # screen, receipt and log keeps working without knowing about players.
        guest_name=', '.join(p['name'] for p in roster)[:100],
        status='active',
        branch_id=table.branch_id,
        receipt_id=random.randint(100000, 999999),
        # The first linked account owns the tab, matching what booking-started
        # sessions already did. Others are recorded but don't claim the bill.
        customer_id=next((p['customerId'] for p in roster if p['customerId']), None),
    )
    db.session.add(session)
    db.session.flush()

    for entry in roster:
        db.session.add(SessionPlayer(
            session_id=session.id,
            name=entry['name'],
            customer_id=entry['customerId'],
        ))

    now = UTC_NOW()
    table.session_id = session.id
    table.is_active = True
    # The joined roster, so every screen that reads booking_name — the station
    # card, the transfer dialog, the canteen's charge-to list — shows who is
    # actually playing without needing to know about the players table.
    table.booking_name = session.guest_name or (booking_name or '').strip()
    table.start_time = now
    open_segment(session, table, now)

    # Adopt a reservation this session is fulfilling. Doing it here rather than
    # relying on the client to call /bookings/<id> afterwards means the link
    # exists no matter what order the requests arrive in.
    window_start = now - timedelta(hours=1)
    window_end = now + timedelta(hours=2)
    pending = (Booking.query
               .filter(Booking.table_uid == table.uid,
                       Booking.status.in_(['booked', 'active']),
                       Booking.start_time <= window_end,
                       Booking.end_time >= window_start)
               .order_by(Booking.start_time)
               .first())
    if pending:
        pending.status = 'active'
        pending.session_id = session.id
        if pending.customer_id:
            session.customer_id = pending.customer_id
            _sp = SessionPlayer.query.filter_by(session_id=session.id).first()
            if _sp and not _sp.customer_id:
                _sp.customer_id = pending.customer_id

    db.session.commit()
    return session


def stop_session(table):
    """Pause play. Nothing is billed and nothing is logged — the tab stays open.

    The receptionist either resumes, or ends the session to settle it.
    """
    session = ensure_session(table)
    now = UTC_NOW()
    if session:
        close_open_segments(session, now)
        session.status = 'stopped'

    table.is_active = False
    table.start_time = None
    # booking_name and session_id are deliberately kept so the tab can be resumed

    db.session.commit()
    if not session:
        return None

    # Preview only: what the tab would cost if settled right now
    invoice = build_invoice(session)
    invoice['resumable'] = True
    invoice['final'] = False
    return invoice


def release_table_bookings(table):
    """Close off any booking still marked in-progress on this station.

    Called on every path that frees a table. A booking left 'active' shows as
    'In progress' to the guest forever AND counts as a clash, so the table can
    never be booked again — one stranded row makes a station unusable.
    """
    return (Booking.query
            .filter(Booking.status == 'active', Booking.table_uid == table.uid)
            .update({'status': 'completed'}, synchronize_session=False))


def end_session(table):
    """Settle the tab: price it, write it to the ledger, and free the station."""
    session = ensure_session(table)
    if not session:
        # Nothing to bill, but the station may still be carrying a stranded
        # booking. Free it rather than leaving the table stuck.
        released = release_table_bookings(table)
        table.is_active = False
        table.start_time = None
        table.session_id = None
        table.booking_name = ''
        db.session.commit()
        return {'nothingToBill': True, 'released': released,
                'settleable': False, 'final': True, 'totalCost': 0,
                'segments': [], 'canteenItems': []} if released else None

    now = UTC_NOW()
    close_open_segments(session, now)  # no-op if already paused

    invoice = build_invoice(session)
    invoice['resumable'] = False
    invoice['final'] = True

    # One token binds the table bill to the canteen orders it carried, so a
    # single payment can clear them all while they stay separately accounted.
    group = f'S{session.id}'
    invoice['billGroup'] = group
    CanteenOrder.query.filter_by(session_id=session.id, payment_method='tab').update(
        {'bill_group': group}, synchronize_session=False
    )

    # Every ended session gets a ledger row, including a very short one.
    #
    # Discarding zero-cost bills seemed tidy but broke the receipt: with no row
    # there is no id, so Paid/On Account had nothing to write to and the QR had
    # no payment to point at — the buttons vanished and the code fell back to
    # the offline merchant payload. A Rs 0 line in the log is a much smaller
    # problem than a receipt that can't be settled.
    log = upsert_log(invoice, session)
    log.bill_group = invoice['billGroup']
    db.session.commit()
    invoice['settleable'] = True

    session.status = 'settled'
    # The guest's booking has now been played and billed. Match on the table as
    # well as the session id: a booking started before its session existed has
    # no session_id, and would otherwise stay 'active' forever and keep the
    # table blocked from future bookings.
    b = Booking.query.filter(Booking.status == 'active',
             db.or_(Booking.session_id == session.id,
                    Booking.table_uid == table.uid)).first()
    
    b.status = 'completed'

    target_url = f"{os.environ.get('CENTRAL_URL')}/api/customer/bookings/sync/{b.sync_id}/completed"
    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.post(target_url)

            if res.status_code not in (200, 201):
                # Parse error message from the remote node
                if res.headers.get("content-type") == "application/json":
                    err_msg = res.json().get("error", res.text)
                else:
                    err_msg = res.text
                    
                # Flask approach: Return a JSON response with the remote status code
                return jsonify({
                    "error": f"Local booking not started because remote node rejected request: {err_msg}"
                }), res.status_code

    except httpx.RequestError as e:
        # Flask approach: Return a 502 Bad Gateway response for connection errors
        return jsonify({
            "error": f"Local booking not started because remote node was unreachable: {str(e)}"
        }), 502
    table.is_active = False
    table.start_time = None
    table.session_id = None
    table.booking_name = ''
    db.session.commit()
    return invoice


def resume_session(table):
    session = PlaySession.query.get(table.session_id) if table.session_id else None
    if not session or session.status != 'stopped':
        return None
    now = UTC_NOW()
    session.status = 'active'
    table.is_active = True
    table.start_time = now
    open_segment(session, table, now)
    db.session.commit()
    return session


# --- ROUTES ---

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.json or {}
    user = User.query.filter_by(username=data.get('username', '').strip(), deleted_at=None).first()
    if not user or not user.check_password(data.get('password', '')):
        return jsonify({'error': 'Invalid username or password'}), 401
    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'role': user.role,
            'username': user.username,
            'capabilities': ','.join(capabilities_for(user)),
        },
    )
    return jsonify({
        'token': token, 'role': user.role, 'username': user.username,
        'capabilities': capabilities_for(user),
    })

@app.route('/api/auth/users', methods=['GET', 'POST'])
def manage_users():
    require_role('owner')
    if request.method == 'GET':
        return jsonify({'users': [
            {
                'id': u.id, 'username': u.username, 'role': u.role,
                'capabilities': capabilities_for(u),
                # Managers and owners cover everything by rank, so the picker
                # should show it rather than invite editing it.
                'capabilitiesLocked': u.role in FULL_ACCESS_ROLES,
                'branchIds': [b.id for b in u.branches],
                'primaryBranchId': u.primary_branch_id,
            }
            for u in User.query.filter_by(deleted_at=None).all()
        ]})
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'receptionist')
    if not username or len(password) < 6 or role not in ROLE_LEVEL:
        return jsonify({'error': 'Username, 6+ char password, and valid role required'}), 400
    if User.query.filter_by(username=username, deleted_at=None).first():
        return jsonify({'error': 'Username already exists'}), 400
    capabilities = parse_capabilities(data.get('capabilities')) or ['floor']
    user = User(username=username, role=role, capabilities=','.join(capabilities))
    user.set_password(password)
    db.session.add(user)
    db.session.flush()                             # need an id before attaching branches
    _assign_branches(user, data.get('branchIds'), data.get('primaryBranchId'))
    db.session.commit()
    return jsonify({'success': True, 'id': user.id,
                    'capabilities': capabilities_for(user)})

@app.route('/api/auth/users/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    require_role('owner')
    user = User.query.get_or_404(user_id)
    data = request.json or {}

    if 'username' in data:
        new_name = data['username'].strip()
        if not new_name:
            return jsonify({'error': 'Username cannot be empty'}), 400
        existing = User.query.filter_by(username=new_name, deleted_at=None).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Username already exists'}), 400
        user.username = new_name

    if data.get('password'):
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in ROLE_LEVEL:
            return jsonify({'error': 'Unknown role'}), 400
        user.role = data['role']

    if 'capabilities' in data:
        chosen = parse_capabilities(data['capabilities'])
        if not chosen and user.role not in FULL_ACCESS_ROLES:
            return jsonify({
                'error': 'Give them at least one counter to work — floor, canteen, or both',
            }), 400
        user.capabilities = ','.join(chosen)

    if 'branchIds' in data or 'primaryBranchId' in data:
        _assign_branches(user, data.get('branchIds', [b.id for b in user.branches]),
                         data.get('primaryBranchId', user.primary_branch_id))
    elif user.role not in ('manager', 'owner') and len(user.branches) > 1:
        _assign_branches(user, [user.primary_branch_id or user.branches[0].id], user.primary_branch_id)

    db.session.commit()
    # Their token still carries the OLD capabilities until they sign in again;
    # say so rather than letting a manager think the change took effect at once.
    return jsonify({
        'success': True, 'username': user.username, 'role': user.role,
        'capabilities': capabilities_for(user),
        'appliesOnNextLogin': True,
    })

def _actor():
    """Username performing the action, stamped onto soft-deleted rows for the audit trail."""
    try:
        return (get_jwt() or {}).get('username') or ''
    except Exception:
        return ''


@app.route('/api/auth/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    require_role('owner')
    user = User.query.get_or_404(user_id)
    if user.role == 'owner' and User.query.filter_by(role='owner', deleted_at=None).count() <= 1:
        return jsonify({'error': 'Cannot delete the last owner'}), 400
    user.deleted_at = datetime.now()
    user.deleted_by = _actor()
    db.session.commit()
    return jsonify({'success': True})


@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(app.static_folder, path)

# Global (per-install) UI preferences, with sane fallbacks for anything not yet
# written. The allowlist is the source of truth: it caps what can be stored and
# what GET reports, so an unknown key can't be injected as a setting.
DEFAULT_SETTINGS = {
    'dashboard_show_bills': True,   # pop the table receipt on checkout
    'canteen_show_bills': True,     # pop the canteen receipt on checkout
    'summary_sticky': False,        # pin the dashboard summary strip to the top
    'allow_active_transfer': False, # allow transferring onto an occupied station (swaps the two tabs)
}


def _setting_on(name):
    """Read a boolean setting, falling back to its default."""
    row = Settings.query.filter_by(setting_name=name).first()
    return bool(row.setting_value) if row is not None else bool(DEFAULT_SETTINGS.get(name, False))


@app.route('/api/settings', methods=['GET'])
def get_settings():
    require_capability('floor')
    stored = {s.setting_name: s.setting_value for s in Settings.query.all()}
    # Merge over defaults so a never-written setting still comes back sensibly.
    return jsonify({'settings': {**DEFAULT_SETTINGS, **{
        k: v for k, v in stored.items() if k in DEFAULT_SETTINGS}}})


@app.route('/api/settings/<setting>', methods=['POST'])
def set_setting(setting):
    require_capability('floor')
    if setting not in DEFAULT_SETTINGS:
        return jsonify({'error': 'Unknown setting'}), 400
    value = bool((request.json or {}).get('value'))
    # Upsert: no seeding step to forget, and no 404 the first time a setting is
    # touched — the row is created on first write.
    row = Settings.query.filter_by(setting_name=setting).first()
    if row is None:
        row = Settings(setting_name=setting, setting_value=value)
        db.session.add(row)
    else:
        row.setting_value = value
    db.session.commit()
    return jsonify({'success': True, 'setting_name': setting, 'setting_value': row.setting_value})

@app.route('/api/branches', methods=['GET'])
def list_branches():
    """Branches the current user may access + the one currently selected. Feeds
    the branch picker; owner sees all, others only their assigned branches."""
    verify_jwt_in_request()
    allowed = set(allowed_branch_ids())
    rows = [b for b in Branch.query.filter_by(deleted_at=None)
            .order_by(Branch.sort_order, Branch.id).all() if b.id in allowed]
    return jsonify({
        'branches': [{**b.to_dict(), 'features': sorted(_features_for_branch(b.id))} for b in rows],
        'selected': selected_branch_id(),
        'selectedFeatures': sorted(_selected_features()),
        'canCombine': len(rows) > 1,   # picker offers "All branches" for reconciliation
    })


@app.route('/api/branches', methods=['POST'])
def create_branch():
    """Owner creates a branch, capped by the licence's branch count."""
    require_role('owner')
    from license_util import licensed_branch_count
    active = Branch.query.filter_by(deleted_at=None).count()
    limit = licensed_branch_count()
    if active >= limit:
        return jsonify({'error': 'branch_limit', 'limit': limit,
                        'message': f'Your licence allows {limit} branch(es). Contact your provider to add more.'}), 403
    data = request.json or {}
    name = (data.get('name') or 'New Branch').strip()[:100] or 'New Branch'
    b = Branch(uid=f"branch-{int(time.time() * 1000)}", name=name,
               address=(data.get('address') or None), status='active', is_default=False,
               sort_order=(db.session.query(db.func.max(Branch.sort_order)).scalar() or 0) + 1)
    db.session.add(b)
    db.session.commit()
    return jsonify(b.to_dict()), 201


@app.route('/api/branches/<int:bid>', methods=['PATCH'])
def rename_branch(bid):
    require_role('owner')
    b = Branch.query.filter_by(id=bid, deleted_at=None).first_or_404()
    data = request.json or {}
    if 'name' in data and (data['name'] or '').strip():
        b.name = data['name'].strip()[:100]
    if 'address' in data:
        b.address = (data['address'] or None)
    db.session.commit()
    return jsonify(b.to_dict())


@app.route('/api/branches/<int:bid>', methods=['DELETE'])
def archive_branch(bid):
    require_role('owner')
    b = Branch.query.filter_by(id=bid, deleted_at=None).first_or_404()
    if b.is_default:
        return jsonify({'error': 'cannot_delete_default'}), 400
    if Branch.query.filter_by(deleted_at=None).count() <= 1:
        return jsonify({'error': 'cannot_delete_last'}), 400
    b.deleted_at = datetime.now()
    b.deleted_by = _current_username()
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/table-types', methods=['GET'])
def get_table_types():
    """Public: the type registry for both the staff and customer frontends."""
    rows = TableType.query.filter_by(is_active=True).order_by(TableType.sort_order).all()
    feats = _selected_features()
    def _entitled(t):
        return t.renderer == 'pool' or t.renderer in feats
    return jsonify([{**t.to_dict(), 'entitled': _entitled(t)} for t in rows])

@app.route('/api/sync/status', methods=['GET'])
def sync_status_ep():
    """Local sync-health snapshot for the UI indicator (mode, backlog, last error)."""
    import sync as _sync
    return jsonify(_sync.sync_status())


@app.route('/api/sync/pull', methods=['GET'])
def sync_pull():
    """Serve a local install its cloud-authoritative changes (online bookings)
    since a cursor. Token-authenticated; the tenant is pinned from that token,
    so RLS scopes the result to the install's club."""
    from tenancy import IS_CLOUD
    if not IS_CLOUD:
        return jsonify({'error': 'not a cloud install'}), 400
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    from license_util import _verified_token
    if not (_verified_token(token) if token else None):
        return jsonify({'error': 'unauthorized'}), 401
    import sync as _sync
    from datetime import datetime as _dtm
    entities = [e for e in (request.args.get('entities', '') or '').split(',') if e]
    since_raw = request.args.get('since') or None
    since = None
    if since_raw:
        try: since = _dtm.fromisoformat(since_raw)
        except ValueError: since = None
    out = _sync.collect_pull(entities or _sync.PULL_ENTITIES, since)
    return jsonify({'entities': out, 'serverTime': _dtm.now().isoformat()})


@app.route('/cloud/session', methods=['POST'])
def cloud_session():
    """Owner signs into the CLOUD app with their signed branch/licence token
    (Ed25519, cloud-verifiable). Returns an owner session JWT that carries the
    club_uid, so every subsequent request is tenant-scoped to their club — this
    is what makes the synced Overview viewable remotely."""
    from tenancy import IS_CLOUD
    if not IS_CLOUD:
        return jsonify({'error': 'not a cloud install'}), 400
    body = request.get_json(silent=True) or {}
    token = (body.get('token') or '').strip()
    from license_util import _verified_token
    claims = _verified_token(token) if token else None
    if not claims or not claims.get('sub'):
        return jsonify({'error': 'Invalid or unverified token.'}), 401
    session_jwt = create_access_token(
        identity=f"owner:{claims['sub']}",
        additional_claims={
            'role': 'owner',
            'username': claims.get('club') or 'Owner',
            'capabilities': 'floor,canteen',
            'club_uid': claims['sub'],
        },
    )
    return jsonify({'token': session_jwt, 'role': 'owner',
                    'username': claims.get('club') or 'Owner',
                    'clubUid': claims['sub']})


@app.route('/api/sync/push', methods=['POST'])
def sync_push():
    """Receive a local install's changes into the cloud DB. Authenticated by the
    install's signed branch/club token; the tenant is pinned from that token by
    the tenancy layer, so RLS + the club_uid default keep every club isolated."""
    from tenancy import IS_CLOUD
    if not IS_CLOUD:
        return jsonify({'error': 'not a cloud install'}), 400
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    from license_util import _verified_token
    claims = _verified_token(token) if token else None
    if not claims:
        return jsonify({'error': 'unauthorized'}), 401
    import sync as _sync
    applied = _sync.apply_push(request.get_json(silent=True) or {})
    return jsonify({'ok': True, 'applied': applied, 'serverTime': datetime.now().isoformat()})


@app.route('/api/branches/overview', methods=['GET'])
def branches_overview():
    """A live, read-only summary for EVERY branch the user may see — the owner's
    comprehensive cross-branch view. Each row is one branch's current pulse."""
    require_capability('floor')
    from datetime import time as _time
    allowed = set(allowed_branch_ids())
    day_start = datetime.combine(datetime.now().date(), _time.min)
    rows = (Branch.query.filter(Branch.id.in_(allowed), Branch.deleted_at.is_(None))
            .order_by(Branch.sort_order, Branch.id).all())
    out = []
    for b in rows:
        tables = PoolTable.query.filter(PoolTable.status != 'deleted', PoolTable.branch_id == b.id).all()
        active = sum(1 for t in tables if t.is_active)
        rev = db.session.query(func.coalesce(func.sum(ActivityLog.total_cost), 0)).filter(
            ActivityLog.branch_id == b.id, ActivityLog.created_at >= day_start).scalar() or 0
        sessions_today = db.session.query(func.count(ActivityLog.id)).filter(
            ActivityLog.branch_id == b.id, ActivityLog.created_at >= day_start).scalar() or 0
        owed = db.session.query(func.coalesce(func.sum(ActivityLog.total_cost), 0)).filter(
            ActivityLog.branch_id == b.id, ActivityLog.payment_status == 'pending').scalar() or 0
        queued = Queue.query.filter_by(deleted_at=None).filter(Queue.branch_id == b.id).count()
        out.append({
            'id': b.id, 'uid': b.uid, 'name': b.name, 'address': b.address or '',
            'tables': len(tables), 'activeTables': active, 'freeTables': len(tables) - active,
            'revenueToday': int(rev), 'sessionsToday': int(sessions_today),
            'owed': int(owed), 'queue': queued,
        })
    total = {
        'revenueToday': sum(r['revenueToday'] for r in out),
        'activeTables': sum(r['activeTables'] for r in out),
        'tables': sum(r['tables'] for r in out),
        'sessionsToday': sum(r['sessionsToday'] for r in out),
        'owed': sum(r['owed'] for r in out),
    }
    return jsonify({'branches': out, 'total': total})


@app.route('/api/state', methods=['GET'])
def get_state():
    require_capability('floor')
    queue = Queue.query.filter_by(deleted_at=None).filter(_branch_scope(Queue)).all()
    tables = PoolTable.query.filter(PoolTable.status != 'deleted').filter(_branch_scope(PoolTable)).order_by(PoolTable.sort_order).all()
    rate_rows = GlobalRate.query.all()
    rates = {r.table_type: {'weekday': r.weekday_rate, 'weekend': r.weekend_rate}
             for r in rate_rows}
    lounges = Lounge.query.filter(Lounge.deleted_at.is_(None)).filter(_branch_scope(Lounge)).all()
    # The dashboard strip lists only what still needs starting.
    active_bookings = Booking.query.filter_by(status='booked').filter(_branch_scope(Booking)).all()
    
    PKT = timezone(timedelta(hours=5))
    PKT_NOW = lambda: datetime.now(PKT).replace(tzinfo=None)

    # Usage in comparison
    now = PKT_NOW()

    def _is_currently_booked(b):
        if not b.start_time:
            return False
        start = b.start_time.astimezone(timezone.utc).replace(tzinfo=None) if b.start_time.tzinfo else b.start_time
        end = b.end_time.astimezone(timezone.utc).replace(tzinfo=None) if (b.end_time and b.end_time.tzinfo) else b.end_time
        if end:
            return start <= now <= end
        return start <= now

    booked_tables = [b.table_uid for b in active_bookings if _is_currently_booked(b)]

    session_status = {s.id: s.status for s in PlaySession.query.all()}

    _feats = _selected_features()
    _renderer_by_type = {tt.key: tt.renderer for tt in TableType.query.all()}
    def _t_entitled(k):
        r = _renderer_by_type.get(k, 'pool')
        return r == 'pool' or r in _feats

    def table_json(t):
        paused = bool(t.session_id) and session_status.get(t.session_id) == 'stopped'
        return {
            'uid': t.uid,
            'id': t.table_id,
            'type': t.table_type,
            'isActive': t.is_active,
            'isBooked': t.uid in booked_tables,
            'loungeUid': t.lounge_uid,
            'bookingName': t.booking_name,
            'players': players_for(t.session_id),
            'startTime': t.start_time.isoformat() + 'Z' if t.start_time else None,
            'sessionId': t.session_id,
            # Time already banked on earlier segments of this tab, so a card can
            # show total elapsed across transfers and pauses instead of restarting.
            'priorSeconds': prior_seconds(t.session_id),
            'entitled': _t_entitled(t.table_type),   # False → licence dropped; lock it
            'resumable': paused,
            # Running total on a paused tab, so the card can show the bill
            # without the receptionist having to settle first.
            'pendingTotal': pending_total(t.session_id) if paused else 0,
        }

    return jsonify({
        'queue': [{'id': q.uid, 'number': q.number, 'guestName': q.guest_name, 'tableType': q.table_type,
                   'loungeUid': q.lounge_uid, 'tableUid': q.table_uid} for q in queue],
        'lounges': [{'id': l.id, 'uid': l.uid, 'name': l.name} for l in lounges],
        'tables': [table_json(t) for t in tables],
        'rates': rates,
        'bookings': [{'id': b.id, 'code': b.code, 'tableUid': b.table_uid, 'guestName': b.guest_name,
                      'startTime': b.start_time.isoformat() if b.start_time else None,
                      'endTime': b.end_time.isoformat() if b.end_time else None,
                      'tableNumber': b.table_number, 'tableType': b.table_type} for b in active_bookings],
    })
@app.route('/api/queue', methods=['POST'])
def add_to_queue():
    require_capability('floor')
    data = request.json or {}
    # Next after the highest still waiting; restarts at 1 once the queue empties
    # (entries are deleted when seated, so max() only sees who's still in line).
    next_number = (db.session.query(db.func.max(Queue.number)).filter(Queue.deleted_at.is_(None)).scalar() or 0) + 1
    db.session.add(Queue(
        guest_name=(data.get('guestName') or '').strip(),   # optional
        table_type=data['tableType'],
        lounge_uid=(data.get('loungeUid') or None),          # null = any lounge
        table_uid=(data.get('tableUid') or None),            # null = any table of the type
        uid=data['uid'],
        number=next_number,
        branch_id=selected_branch_id(),
    ))
    db.session.commit()
    return jsonify({'success': True, 'number': next_number})

@app.route('/api/queue/<int:uid>', methods=['DELETE'])
def remove_from_queue(uid):
    require_capability('floor')
    q = Queue.query.filter_by(uid=uid).first_or_404()
    q.deleted_at = datetime.now()
    q.deleted_by = _actor()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/tables', methods=['POST'])
def add_table():
    require_role('manager')
    data = request.json
    uid = f"{data['type']}-{int(time.time() * 1000)}"
    
    _tt = TableType.query.filter_by(key=data['type'], is_active=True).first()
    if _tt is None:
        return jsonify({'error': 'invalid_type'}), 400          # unknown type → reject
    if _tt.renderer != 'pool' and _tt.renderer not in _selected_features():
        return jsonify({'error': 'feature_not_licensed', 'feature': _tt.renderer}), 403
    sort_orders = PoolTable.query.filter_by(lounge_uid=data.get('loungeUid')).all() or []
    if sort_orders == []:
        sort_order = 0
    else:
        sort_order = max([table.sort_order for table in sort_orders]) + 1
    db.session.add(PoolTable(uid=uid, table_id=data['id'], table_type=data['type'], is_active=False, booking_name='', start_time=None, lounge_uid=data.get('loungeUid'), status='active', branch_id=selected_branch_id(), sort_order=sort_order))
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/tables/<uid>', methods=['DELETE'])
def delete_table(uid):
    require_role('manager')
    table = PoolTable.query.filter_by(uid=uid).first_or_404()
    table.status = 'deleted'
    table.deleted_at = datetime.now()
    table.deleted_by = _actor()
    # db.session.delete(PoolTable.query.filter_by(uid=uid).first_or_404())
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/customers/lookup', methods=['GET'])
def lookup_customer():
    """Find an account by phone, so staff can link a player to it.

    Returns only what the counter needs to confirm they've got the right
    person — name and a masked number. Staff can already see who is playing;
    they have no reason to be handed an email or a full contact list, and a
    lookup that dumped account details would turn a phone number into a
    directory of the club's customers.
    """
    require_capability('floor')

    # Imported here, not at module scope: customer_api is only registered when
    # this process serves the customer side, but staff always need to look a
    # number up in the same canonical form the accounts were stored in.
    from customer_api import normalise_phone

    phone = normalise_phone(request.args.get('phone', ''))
    if not phone:
        return jsonify({'error': 'Enter a valid mobile number'}), 400

    customer = Customer.query.filter_by(phone=phone).first()
    if not customer or not customer.is_active:
        return jsonify({'found': False, 'error': 'No account with that number'}), 404

    return jsonify({
        'found': True,
        'customer': {
            'id': customer.id,
            'name': customer.name,
            # Enough to check it's the right person, not enough to harvest.
            'phone': f'••••••{customer.phone[-4:]}',
        },
    })


@app.route('/api/tables/toggle', methods=['POST'])
def toggle_table():
    require_capability('floor')
    data = request.json
    table = PoolTable.query.filter_by(uid=data['uid']).first_or_404()

    if data['isActive']:
        if not _type_entitled(table.table_type, table.branch_id):
            return jsonify({'error': 'feature_not_licensed', 'feature': table.table_type}), 403
        session = start_session(table, data.get('bookingName'), data.get('players'))
        return jsonify({
            'success': True,
            'sessionId': session.id,
            'startTime': table.start_time.isoformat() + 'Z',
            'priorSeconds': 0,
        })

    invoice = stop_session(table)
    return jsonify({'success': True, 'invoice': invoice})


@app.route('/api/tables/<uid>/stop', methods=['POST'])
def stop_table(uid):
    """Pause play. Returns a preview of the bill so far; settles nothing."""
    require_capability('floor')
    table = PoolTable.query.filter_by(uid=uid).first_or_404()
    if not table.is_active:
        return jsonify({'error': 'Station is not running'}), 400
    invoice = stop_session(table)
    if invoice is None:
        return jsonify({'error': 'Nothing to bill'}), 400
    return jsonify({'success': True, 'invoice': invoice})


@app.route('/api/bills/<int:log_id>/settle', methods=['POST'])
def settle_bill(log_id):
    """Settle a table bill — and anything charged to the same tab.

    'khata' leaves it pending under a name (a running credit account); 'paid'
    records the method; 'pending' undoes a mis-tap.
    """
    require_capability('floor')
    log = ActivityLog.query.get_or_404(log_id)
    data = request.json or {}
    status = data.get('status')
    method = data.get('method') or 'cash'

    logs, orders = ([log], [])
    if log.bill_group:
        logs, orders = group_bills(log.bill_group)

    if status == 'paid':
        paid = settle_bills(logs=logs, orders=orders, method=method)
    elif status == 'pending':
        # Undo everything, including the account it was charged to. `payer=None`
        # means "leave the name alone", which quietly kept the bill on that
        # guest's account while claiming to be unsettled.
        settle_bills(logs=logs, orders=orders, status='pending', payer='')
        paid = 0
    elif status == 'khata':
        name = ((data.get('name') or '').strip() or log.player or '').strip()
        if not name or name.lower() == 'walk-in guest':
            return jsonify({
                'error': 'An account needs a name — take payment at the counter instead',
            }), 400
        settle_bills(logs=logs, orders=orders, status='pending', payer=name)
        paid = 0
    else:
        return jsonify({'error': 'Status must be paid, pending or khata'}), 400

    return jsonify({
        'logId': log.id,
        'paymentStatus': log.payment_status,
        'paymentMethod': log.payment_method,
        'khataName': log.khata_name,
        'paid': paid,
        # So the till can say "cleared 2 bills", not just one.
        'billsSettled': len(logs) + len(orders),
    })


@app.route('/api/khata', methods=['GET'])
def khata_book():
    """Everything still owed, grouped by who owes it.

    Covers BOTH ledgers: table bills left on credit and canteen sales put on a
    khata. A guest who owes for a frame and a packet of crisps should appear
    once with one number, not twice.
    """
    require_role('manager')

    people = {}

    def bucket(name):
        key = (name or 'Unknown').strip() or 'Unknown'
        return people.setdefault(key, {'name': key, 'total': 0, 'bills': []})

    # Only bills actually PUT on an account. A pending bill with no name is
    # simply unpaid and belongs on the Active Bills page — listing it here made
    # every fresh bill look like somebody's debt, under the guest's name.
    for row in ActivityLog.query.filter(
            _branch_report_scope(ActivityLog),
            ActivityLog.payment_status == 'pending',
            ActivityLog.khata_name.isnot(None),
            ActivityLog.khata_name != '').order_by(ActivityLog.id.desc()).all():
        entry = bucket(row.khata_name)
        entry['total'] += row.total_cost
        entry['bills'].append({
            'kind': 'session', 'id': row.id, 'ref': row.receipt_id, 'date': row.date_string,
            'label': f'{(row.table_type or "").title()} #{row.table_id}',
            'total': row.total_cost,
            # Per bill, so a guest can clear one debt without paying the lot —
            # scanning settles exactly that bill and nothing else.
            'payUrl': ensure_pay_link(
                amount=row.total_cost, kind='session', reference=str(row.receipt_id),
                payer_name=row.khata_name or row.player or '', log_id=row.id,
            ),
        })

    # Tab orders belong here too now that they are bills in their own right —
    # but only once their session has ended (bill_group is set). While a table
    # is still running the order is an open tab, not a debt.
    for order in CanteenOrder.query.filter(
            CanteenOrder.status == 'paid',
            CanteenOrder.payment_status == 'pending',
            db.or_(CanteenOrder.payment_method != 'tab',
                   CanteenOrder.bill_group.isnot(None))).order_by(CanteenOrder.id.desc()).all():
        # Only named credit belongs in the book; an unpaid counter sale with no
        # name is a till mistake, not a debt anyone can be chased for.
        if not order.khata_name:
            continue
        entry = bucket(order.khata_name)
        entry['total'] += order.total
        entry['bills'].append({
            'kind': 'canteen', 'id': order.id, 'ref': order.order_no,
            'date': order.created_at.isoformat() if order.created_at else '',
            'label': 'Canteen', 'total': order.total,
            'payUrl': ensure_pay_link(
                amount=order.total, kind='canteen', reference=order.order_no,
                payer_name=order.khata_name or '', order_id=order.id,
            ),
        })

    ordered = sorted(people.values(), key=lambda p: -p['total'])
    for entry in ordered:
        entry['bills'].sort(key=lambda b: b['date'], reverse=True)

    return jsonify({
        'outstanding': sum(p['total'] for p in ordered),
        'people': ordered,
    })


# ─── PAYMENTS (DEMO) ─────────────────────────────────────────────────────────
#
# A payment intent is a small record a QR code can point at. Scanning opens a
# public page showing what's owed; confirming there marks it paid and pings the
# till. No gateway is involved yet — `confirm_payment` is where a real
# EasyPaisa/JazzCash callback would land, and everything either side of it is
# already in place.

PAYMENT_METHODS_PUBLIC = ('easypaisa', 'jazzcash')


def public_base_url():
    """Origin a phone should open, taken from the request that created the QR.

    A LAN tablet reaches the server on its IP, so hardcoding localhost would
    produce a QR that only works on the machine that printed it.
    """
    configured = os.environ.get('PUBLIC_BASE_URL')
    if configured:
        return configured.rstrip('/')
    return request.host_url.rstrip('/')


def intent_json(intent, include_url=True):
    payload = {
        'token': intent.token,
        'kind': intent.kind,
        'reference': intent.reference,
        'amount': intent.amount,
        'payerName': intent.payer_name,
        'paidBy': intent.paid_by,
        'method': intent.method,
        'status': intent.status,
        'createdAt': intent.created_at.isoformat() if intent.created_at else None,
        'paidAt': intent.paid_at.isoformat() if intent.paid_at else None,
        # So an open receipt can tell whether THIS payment was for it.
        'logId': intent.log_id,
        'orderId': intent.canteen_order_id,
        'billGroup': (ActivityLog.query.get(intent.log_id).bill_group
                      if intent.log_id else None),
    }
    if include_url:
        payload['payUrl'] = f'{public_base_url()}/pay/{intent.token}'
    return payload


# ─── BILLING ─────────────────────────────────────────────────────────────────
#
# Two ledgers, one settlement path.
#
#   ActivityLog   a TABLE bill — play time only.
#   CanteenOrder  a CANTEEN bill — food and drink.
#
# When a canteen order rides a table's tab, both rows share a `bill_group`. The
# guest is handed one combined total; the books keep the two apart so canteen
# takings are never reported as table takings. Settling any member of a group
# settles the whole group, because the guest paid once.
#
# Every route that takes money funnels through settle_bills(), so status,
# method and timestamp can never disagree between the two ledgers.

PAYMENT_METHODS = ('cash', 'easypaisa', 'jazzcash', 'account')


def group_bills(group):
    """Every bill sharing a group token."""
    if not group:
        return [], []
    logs = ActivityLog.query.filter_by(bill_group=group).all()
    orders = (CanteenOrder.query
              .filter(CanteenOrder.bill_group == group, CanteenOrder.status != 'void')
              .all())
    return logs, orders


def settle_bills(*, logs=(), orders=(), method='cash', payer=None, status='paid'):
    """Mark bills paid (or put them back to pending) in one place.

    Returns the amount that actually changed hands, so callers never have to
    re-derive it and risk reporting a figure the ledger disagrees with.
    """
    if method not in PAYMENT_METHODS:
        method = 'cash'
    now = datetime.now()
    moved = 0

    for row in logs:
        if status == 'paid':
            if row.payment_status == 'paid':
                continue
            row.payment_status = 'paid'
            row.payment_method = method
            row.settled_at = now
            row.khata_name = None
            moved += row.total_cost
        else:
            row.payment_status = 'pending'
            row.payment_method = ''
            row.settled_at = None
            if payer is not None:
                row.khata_name = payer or None

    for order in orders:
        if order.status == 'void':
            continue
        if status == 'paid':
            if order.payment_status == 'paid':
                continue
            order.payment_status = 'paid'
            order.payment_method = method
            order.settled_at = now
            order.khata_name = None
            moved += order.total
        else:
            order.payment_status = 'pending'
            order.settled_at = None
            if payer is not None:
                order.khata_name = payer or None

    db.session.commit()
    return moved


def settle_group(group, *, method='cash'):
    """One payment clears a table bill and everything charged to its tab."""
    logs, orders = group_bills(group)
    return settle_bills(logs=logs, orders=orders, method=method)


def ensure_pay_link(*, amount, kind, reference='', payer_name='',
                    log_id=None, order_id=None, customer_id=None):
    """Get (or mint) the payment URL for a bill.

    Called wherever a bill is produced, so a receipt arrives with its QR already
    resolved. Doing this lazily in the browser meant the code rendered before
    the link existed and silently fell back to the offline merchant payload —
    which is why scanning gave an EasyPaisa number instead of opening the app.
    """
    if not amount or amount <= 0:
        return None
    # Automated EasyPaisa/JazzCash (the payment aggregator) is a licensed add-on.
    # Without the 'payments' entitlement no QR is minted, so the receipt falls
    # back to manual "Paid EasyPaisa/JazzCash" marking instead.
    from license_util import licensed_features
    if 'payments' not in _selected_features():
        return None

    existing = None
    if log_id:
        existing = PaymentIntent.query.filter_by(log_id=log_id, status='pending').first()
    elif order_id:
        existing = PaymentIntent.query.filter_by(canteen_order_id=order_id, status='pending').first()
    elif customer_id and kind == 'account':
        existing = PaymentIntent.query.filter_by(
            customer_id=customer_id, kind='account', status='pending').first()

    if existing:
        if existing.amount != amount:
            existing.amount = amount
            db.session.commit()
        return f'{public_base_url()}/pay/{existing.token}'

    intent = PaymentIntent(
        token=secrets.token_urlsafe(12), kind=kind,
        reference=str(reference or '')[:40], amount=amount,
        payer_name=str(payer_name or '')[:100],
        log_id=log_id, canteen_order_id=order_id, customer_id=customer_id,
    )
    db.session.add(intent)
    db.session.commit()
    return f'{public_base_url()}/pay/{intent.token}'


if SERVE_STAFF:
    # Registered here, not at import time: the canteen routes need
    # ensure_pay_link, which is defined just above.
    register_canteen_routes(app, require_role, _current_username, ensure_pay_link, require_capability=require_capability,
                            selected_branch=selected_branch_id, branch_scope=_branch_scope, branch_report_scope=_branch_report_scope,)

    # ── Licensing ────────────────────────────────────────────────────────────
    from license_api import register_license_routes
    from license_util import is_licensed, licensed_features, branch_features, active_branch_license
    register_license_routes(app, require_role)

    # SERVER-SIDE enforcement — the real security boundary (a patched frontend
    # or flipped env can't bypass it). Without a valid, server-verified license
    # EVERY /api route (staff, canteen, customer) returns 403. Only the minimum
    # needed to sign in and activate stays reachable pre-license.
    _LICENSE_ALLOW = ("/api/auth/login", "/api/logout", "/api/license", "/api/branding")

    @app.before_request
    def _enforce_license():
        if request.method == "OPTIONS":
            return
        path = request.path
        if not path.startswith("/api"):
            return                      # static assets serve freely (the gate UI needs them)
        if any(path.startswith(p) for p in _LICENSE_ALLOW):
            return
        if not is_licensed():           # crypto + device + heartbeat/revocation check
            return jsonify({"error": "license_required"}), 403
        # Feature gate: module endpoints require the licence to grant that module.
        feats = _selected_features()
        for prefix, feat in (("/api/canteen", "canteen"), ("/api/bookings", "bookings"), ("/api/insights", "insights")):
            if path.startswith(prefix) and feat not in feats:
                return jsonify({"error": "feature_not_licensed", "feature": feat}), 403

if SERVE_CUSTOMER:
    # Same helper for guest-facing codes, so a bill's QR is identical whether
    # it's scanned off a printed receipt or out of the app.
    customer_api.set_pay_link(ensure_pay_link)


@app.route('/api/payments/intent', methods=['POST'])
def create_payment_intent():
    """Mint (or reuse) the intent a receipt's QR should point at."""
    require_capability('floor', 'canteen')  # both counters take money
    data = request.json or {}

    try:
        amount = int(data.get('amount') or 0)
    except (TypeError, ValueError):
        return jsonify({'error': 'Amount must be a number'}), 400
    if amount <= 0:
        return jsonify({'error': 'Nothing to pay'}), 400

    kind = data.get('kind') if data.get('kind') in ('session', 'canteen', 'account') else 'session'
    log_id = data.get('logId')
    order_id = data.get('orderId')

    # Reissuing a receipt shouldn't spawn a second QR for the same bill.
    existing = None
    if log_id:
        existing = PaymentIntent.query.filter_by(log_id=log_id, status='pending').first()
    elif order_id:
        existing = PaymentIntent.query.filter_by(canteen_order_id=order_id, status='pending').first()
    if existing:
        if existing.amount != amount:
            existing.amount = amount
            db.session.commit()
        return jsonify({'intent': intent_json(existing)})

    intent = PaymentIntent(
        token=secrets.token_urlsafe(12),
        kind=kind,
        reference=str(data.get('reference') or '')[:40],
        amount=amount,
        payer_name=str(data.get('payerName') or '')[:100],
        log_id=log_id,
        canteen_order_id=order_id,
        customer_id=data.get('customerId'),
    )
    db.session.add(intent)
    db.session.commit()
    return jsonify({'intent': intent_json(intent)}), 201


@app.route('/api/pay/<token>', methods=['GET'])
def public_payment(token):
    """What a scanned QR shows. Deliberately unauthenticated — whoever holds
    the code is at the counter with the bill in front of them.

    Only the amount and a reference are exposed: no phone number, no itemised
    history, nothing that would matter if the link were forwarded.
    """
    intent = PaymentIntent.query.filter_by(token=token).first()
    if not intent:
        return jsonify({'error': 'That payment link is not valid'}), 404
    return jsonify({'payment': intent_json(intent, include_url=False)})


@app.route('/api/pay/<token>/confirm', methods=['POST'])
def confirm_payment(token):
    """DEMO stand-in for a gateway callback.

    A real integration would verify a signed webhook here instead of trusting
    the caller; everything downstream — settling the bill, pinging the till —
    stays exactly the same.
    """
    intent = PaymentIntent.query.filter_by(token=token).first()
    if not intent:
        return jsonify({'error': 'That payment link is not valid'}), 404
    if intent.status == 'paid':
        # Re-scanning a paid code shouldn't double-ping the till.
        return jsonify({'payment': intent_json(intent, include_url=False), 'alreadyPaid': True})

    data = request.json or {}
    method = data.get('method') if data.get('method') in PAYMENT_METHODS_PUBLIC else 'easypaisa'
    intent.method = method
    intent.paid_by = (str(data.get('paidBy') or '').strip() or intent.payer_name or 'Guest')[:100]
    intent.status = 'paid'
    intent.paid_at = datetime.now()

    # Settle whatever the intent was raised against — through the same path the
    # till uses, so a QR payment and a cash payment leave identical records.
    if intent.log_id:
        log = ActivityLog.query.get(intent.log_id)
        if log:
            if log.bill_group:
                settle_group(log.bill_group, method=method)
            else:
                settle_bills(logs=[log], method=method)
    elif intent.canteen_order_id:
        order = CanteenOrder.query.get(intent.canteen_order_id)
        if order:
            if order.bill_group:
                settle_group(order.bill_group, method=method)
            else:
                settle_bills(orders=[order], method=method)
    elif intent.kind == 'account' and intent.customer_id:
        # Paying off a balance clears every bill behind it, both ledgers.
        customer = db.session.get(Customer, intent.customer_id)
        logs = ActivityLog.query.filter(
            ActivityLog.payment_status == 'pending',
            ActivityLog.customer_id == intent.customer_id,
        ).all()
        orders = []
        if customer and customer.name:
            orders = CanteenOrder.query.filter(
                CanteenOrder.payment_status == 'pending',
                CanteenOrder.status != 'void',
                db.func.lower(CanteenOrder.khata_name) == customer.name.strip().lower(),
            ).all()
        settle_bills(logs=logs, orders=orders, method=method)

    db.session.commit()
    return jsonify({'payment': intent_json(intent, include_url=False)})


@app.route('/api/payments/recent', methods=['GET'])
def recent_payments():
    """Payments the till hasn't announced yet.

    Marking them seen on read means each payment pings once, even with the
    dashboard and the canteen both polling.
    """
    require_capability('floor', 'canteen')  # both counters take money
    unseen = (PaymentIntent.query
              .filter(PaymentIntent.status == 'paid', PaymentIntent.seen_at.is_(None))
              .order_by(PaymentIntent.paid_at)
              .all())
    payments = [intent_json(i, include_url=False) for i in unseen]
    if unseen:
        now = datetime.now()
        for intent in unseen:
            intent.seen_at = now
        db.session.commit()
    return jsonify({'payments': payments})


@app.route('/api/bills/active', methods=['GET'])
def active_bills():
    """Bills awaiting a decision at the counter, newest first.

    Both an unpaid bill and one on account are still money owed — the
    difference is whether anyone has said HOW it will be collected. A bill on
    account has an owner and is chased through the credit book; this page is
    for bills where that hasn't been settled yet, so the two don't bury each
    other.

    `?include=all` returns everything outstanding when the total owed matters
    more than the split.

    Each bill is returned in the shape BillingReceipt renders, so the page can
    show real receipts rather than a summary table.
    """
    require_capability('floor')

    # Open means not yet closed. A bill the counter has finished with is gone
    # from here whether it was paid or put on an account; one that is still on
    # screen is still somebody's job, even if the money has been taken.
    rows = (ActivityLog.query
            .filter(ActivityLog.closed_at.is_(None))
            .order_by(ActivityLog.id.desc())
            .all())

    bills = []
    for log in rows:
        group_orders = []
        if log.bill_group:
            group_orders = (CanteenOrder.query
                            .filter(CanteenOrder.bill_group == log.bill_group,
                                    CanteenOrder.status != 'void')
                            .all())
        canteen_items = parse_segments(log.canteen_json)
        canteen_total = log.canteen_total or sum(o.total for o in group_orders)

        bills.append({
            'logId': log.id,
            'receiptId': log.receipt_id,
            'date': log.date_string,
            'lounge': log.lounge,
            'tableType': log.table_type,
            'tableId': log.table_id,
            'player': log.player,
            'isWalkIn': not (log.player or '').strip()
            or (log.player or '').lower() == 'walk-in guest',
            'elapsed': log.elapsed,
            'billableMins': log.billable_mins,
            'rate': log.rate,
            'segments': parse_segments(log.segments_json),
            'canteenItems': canteen_items,
            'playTotal': log.play_total if log.play_total is not None else log.total_cost,
            'canteenTotal': canteen_total,
            # What the guest owes: their table time plus anything on the tab.
            'totalCost': log.total_cost + canteen_total,
            'splitCount': log.split_count or 1,
            'paymentStatus': log.payment_status,
            'servedBy' : log.served_by,
            'paymentMethod': log.payment_method or '',
            'khataName': log.khata_name,
            'billGroup': log.bill_group,
            'settleable': True,
            'closedAt': log.closed_at.isoformat() if log.closed_at else None,
            'payUrl': ensure_pay_link(
                amount=log.total_cost + canteen_total, kind='session',
                reference=str(log.receipt_id), payer_name=log.player or '',
                log_id=log.id,
            ),
        })

    # Money still owed anywhere, so the page can report it without listing
    # bills that have already been closed.
    owed = ActivityLog.query.filter(ActivityLog.payment_status == 'pending').all()

    return jsonify({
        'bills': bills,
        'awaitingPayment': sum(b['totalCost'] for b in bills
                               if b['paymentStatus'] != 'paid' and not b['khataName']),
        'onAccount': sum(r.total_cost for r in owed if (r.khata_name or '').strip()),
        'totalOwed': sum(r.total_cost for r in owed),
        'outstanding': sum(b['totalCost'] for b in bills),
    })


@app.route('/api/bills/<int:log_id>', methods=['GET'])
def bill_status(log_id):
    """Current settlement state of one bill.

    An open receipt polls this so it reflects a QR payment on its own. It
    deliberately does NOT rely on the payment-notification feed: those are
    consumed by whichever screen polls first, so a receipt watching that feed
    would miss payments announced to the canteen till instead.
    """
    require_capability('floor')
    log = ActivityLog.query.get_or_404(log_id)
    return jsonify({
        'logId': log.id,
        'paymentStatus': log.payment_status,
        'paymentMethod': log.payment_method or '',
        'khataName': log.khata_name,
        'splitCount': log.split_count or 1,
    })


@app.route('/api/bills/<int:log_id>/close', methods=['POST'])
def close_bill(log_id):
    """Finish with a bill: take it off the counter for good.

    Only a settled bill can be closed — paid, or placed on somebody's account.
    Otherwise closing would be a way to make money owed disappear from every
    screen at once, which is exactly what the Active Bills page exists to
    prevent. Anything charged to the same tab closes with it.
    """
    require_capability('floor')
    log = ActivityLog.query.get_or_404(log_id)

    settled = log.payment_status == 'paid' or bool((log.khata_name or '').strip())
    if not settled:
        return jsonify({
            'error': 'Take payment, or put this on an account, before closing it',
        }), 409

    if log.closed_at:
        return jsonify({'logId': log.id, 'closedAt': log.closed_at.isoformat(),
                        'alreadyClosed': True})

    now = datetime.now()
    who = _current_username()
    logs, orders = ([log], [])
    if log.bill_group:
        logs, orders = group_bills(log.bill_group)

    for row in logs:
        row.closed_at = now
        row.closed_by = who
    for order in orders:
        order.closed_at = now
        order.closed_by = who
    db.session.commit()

    return jsonify({
        'logId': log.id,
        'closedAt': now.isoformat(),
        'closedBy': who,
        'billsClosed': len(logs) + len(orders),
    })


@app.route('/api/bills/<int:log_id>/reopen', methods=['POST'])
def reopen_bill(log_id):
    """Put a closed bill back on the counter — a closure was a mistake."""
    require_role('manager')
    log = ActivityLog.query.get_or_404(log_id)
    logs, orders = ([log], [])
    if log.bill_group:
        logs, orders = group_bills(log.bill_group)
    for row in list(logs) + list(orders):
        row.closed_at = None
        row.closed_by = None
    db.session.commit()
    return jsonify({'logId': log.id, 'reopened': True})


@app.route('/api/bills/<int:log_id>/split', methods=['POST'])
def set_bill_split(log_id):
    """Remember how many ways a bill was split.

    Kept on the ledger row so reopening the receipt shows the same per-head
    figure the guests actually paid, rather than resetting to one.
    """
    require_capability('floor')
    log = ActivityLog.query.get_or_404(log_id)
    raw = (request.json or {}).get('splitCount')
    # `or 1` would quietly turn a rejected 0 into a valid 1, so check the value
    # that was actually sent.
    if raw is None:
        return jsonify({'error': 'Split count required'}), 400
    try:
        count = int(raw)
    except (TypeError, ValueError):
        return jsonify({'error': 'Split must be a whole number'}), 400
    if count < 1 or count > 50:
        return jsonify({'error': 'Split must be between 1 and 50'}), 400

    log.split_count = count
    db.session.commit()
    return jsonify({'logId': log.id, 'splitCount': count})


@app.route('/api/khata/settle', methods=['POST'])
def settle_khata():
    """Take payment against someone's credit.

    Settles whole bills oldest-first. Partial payment isn't supported on
    purpose: a bill is either paid or it isn't, and splitting one across two
    payments would leave a receipt that can't say which it is.
    """
    require_capability('floor')
    data = request.json or {}
    wanted_sessions = set(data.get('sessionIds') or [])
    wanted_orders = set(data.get('orderIds') or [])

    # Settling specific bills is identified by the bills themselves; a name is
    # only needed when clearing somebody's whole account.
    method = data.get('method') or 'cash'

    if wanted_sessions or wanted_orders:
        logs = ActivityLog.query.filter(
            ActivityLog.id.in_(wanted_sessions),
            ActivityLog.payment_status == 'pending').all()
        orders = CanteenOrder.query.filter(
            CanteenOrder.id.in_(wanted_orders),
            CanteenOrder.payment_status == 'pending').all()
        # Settling one member of a tab settles the tab: the guest paid once.
        for row in list(logs) + list(orders):
            if row.bill_group:
                more_logs, more_orders = group_bills(row.bill_group)
                logs = list({r.id: r for r in list(logs) + more_logs}.values())
                orders = list({o.id: o for o in list(orders) + more_orders}.values())
        paid = settle_bills(logs=logs, orders=orders, method=method)
        if not paid:
            return jsonify({'error': 'Those bills are already settled'}), 404
        return jsonify({'success': True, 'paid': paid,
                        'billsSettled': len(logs) + len(orders)})

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Whose account?'}), 400

    sessions = (ActivityLog.query
                .filter(ActivityLog.payment_status == 'pending',
                        db.func.lower(db.func.coalesce(ActivityLog.khata_name, ActivityLog.player))
                        == name.lower())
                .order_by(ActivityLog.id)
                .all())
    orders = (CanteenOrder.query
              .filter(CanteenOrder.status == 'paid',
                      CanteenOrder.payment_status == 'pending',
                      CanteenOrder.payment_method != 'tab',
                      db.func.lower(CanteenOrder.khata_name) == name.lower())
              .order_by(CanteenOrder.id)
              .all())

    if not sessions and not orders:
        return jsonify({'error': 'Nothing outstanding for that name'}), 404

    paid = settle_bills(logs=sessions, orders=orders, method=method)

    remaining = (sum(r.total_cost for r in sessions if r.payment_status == 'pending')
                 + sum(o.total for o in orders if o.payment_status == 'pending'))
    return jsonify({'success': True, 'name': name, 'paid': paid, 'remaining': remaining})


@app.route('/api/tables/<uid>/end', methods=['POST'])
def end_table(uid):
    """Settle the tab, write the receipt to the ledger and free the station."""
    require_capability('floor')
    table = PoolTable.query.filter_by(uid=uid).first_or_404()
    # Deliberately no "nothing open" guard: a table with no session can still be
    # carrying a booking stuck at 'active', and refusing here is what left those
    # stations permanently unbookable. end_session cleans up and returns None
    # when there was genuinely nothing to do.
    invoice = end_session(table)
    if invoice and invoice.get('logId'):
        invoice['payUrl'] = ensure_pay_link(
            amount=invoice.get('totalCost'), kind='session',
            reference=str(invoice.get('receiptId') or ''),
            payer_name=invoice.get('player') or '',
            log_id=invoice['logId'], customer_id=invoice.get('customerId'),
        )
    if invoice is None:
        # Nothing was running and nothing was stranded — the station is already
        # free, so this is a no-op rather than an error the user must clear.
        return jsonify({'success': True, 'invoice': None})
    return jsonify({'success': True, 'invoice': invoice})


@app.route('/api/tables/<uid>/resume', methods=['POST'])
def resume_table(uid):
    """Reopen a stopped tab on this station and keep accumulating on the same bill."""
    require_capability('floor')
    table = PoolTable.query.filter_by(uid=uid).first_or_404()
    if table.is_active:
        return jsonify({'error': 'Station is already running'}), 400
    session = resume_session(table)
    if not session:
        return jsonify({'error': 'No stopped session to resume on this station'}), 400
    return jsonify({
        'success': True,
        'sessionId': session.id,
        'bookingName': table.booking_name,
        'startTime': table.start_time.isoformat() + 'Z',
        'priorSeconds': prior_seconds(session.id),
    })


@app.route('/api/tables/transfer', methods=['POST'])
def transfer_table():
    require_capability('floor')
    data = request.json
    from_table = PoolTable.query.filter_by(uid=data['from_uid']).first_or_404()
    to_table = PoolTable.query.filter_by(uid=data['to_uid']).first_or_404()

    if from_table.uid == to_table.uid:
        return jsonify({'error': 'Pick a different destination station'}), 400
    if not from_table.is_active:
        return jsonify({'error': 'Source station is not running'}), 400

    session = ensure_session(from_table)
    if not session:
        return jsonify({'error': 'No session to transfer'}), 400

    now = UTC_NOW()

    # ── Destination occupied → swap the two tabs (guarded by the setting) ──
    if to_table.is_active:
        # The request may pass allowActive for a per-transfer confirm; otherwise
        # fall back to the persisted "switch to active tables" setting.
        allow = bool((data or {}).get('allowActive')) or _setting_on('allow_active_transfer')
        if not allow:
            return jsonify({'error': 'Destination station is already occupied'}), 400
        to_session = ensure_session(to_table)
        if not to_session:
            return jsonify({'error': 'Destination station has no session to swap'}), 400

        # Snapshot both tabs before we overwrite either station.
        from_name, from_sid = from_table.booking_name, session.id
        to_name, to_sid = to_table.booking_name, to_session.id

        # Each session closes its current stretch and re-opens one at its NEW
        # station, so both tabs keep billing correctly across the swap.
        close_open_segments(session, now)
        close_open_segments(to_session, now)
        open_segment(session, to_table, now)      # from-tab moves onto to_table
        open_segment(to_session, from_table, now) # to-tab moves onto from_table

        to_table.booking_name, to_table.session_id, to_table.start_time = from_name, from_sid, now
        from_table.booking_name, from_table.session_id, from_table.start_time = to_name, to_sid, now
        # both remain is_active = True

        db.session.commit()
        return jsonify({
            'success': True,
            'swapped': True,
            'startTime': now.isoformat() + 'Z',
            'priorSeconds': prior_seconds(session.id),
            'sessionId': session.id,
            'swappedWith': {'uid': from_table.uid, 'sessionId': to_sid,
                            'startTime': now.isoformat() + 'Z',
                            'priorSeconds': prior_seconds(to_sid)},
        })

    # ── Destination free → plain transfer (unchanged behaviour) ──
    # Close the stretch on the old station and open a fresh one on the new
    # station at ITS rate — this is what makes mixed-station tabs bill correctly.
    close_open_segments(session, now)
    open_segment(session, to_table, now)

    to_table.is_active = True
    to_table.start_time = now
    to_table.booking_name = from_table.booking_name
    to_table.session_id = session.id

    from_table.is_active = False
    from_table.start_time = None
    from_table.booking_name = ''
    from_table.session_id = None

    db.session.commit()
    return jsonify({
        'success': True,
        'swapped': False,
        'startTime': now.isoformat() + 'Z',
        'priorSeconds': prior_seconds(session.id),
        'sessionId': session.id,
    })

# Shortest bookable slot. Kept in step with MIN_DURATION_MINUTES in
# frontend/src/utils/bookingTime.js — change both together.
MIN_BOOKING_MINUTES = 30


@app.route('/api/bookings', methods=['GET', 'POST'])
def handle_bookings():
    require_capability('floor')  # any logged-in user
    if request.method == 'POST':
        data = request.json or {}
        try:
            start = datetime.fromisoformat(data['startTime'])  # local ISO from the client
            end = datetime.fromisoformat(data['endTime'])
        except (KeyError, ValueError):
            return jsonify({'error': 'Valid start and end times are required'}), 400

        if not data.get('guestName', '').strip():
            return jsonify({'error': 'Guest name required'}), 400

        # The client disables these, but a request can arrive from anywhere, and
        # a stale tab can post a slot that has since gone by.
        if end <= start:
            return jsonify({'error': 'End time must be after the start time'}), 400
        duration = (end - start).total_seconds() / 60
        if duration < MIN_BOOKING_MINUTES:
            return jsonify({'error': f'Minimum booking is {MIN_BOOKING_MINUTES} minutes'}), 400
        # One slot of slack, so a booking made right on the hour isn't rejected
        # for being a few seconds stale by the time it lands.
        if start < datetime.now() - timedelta(minutes=1):
            return jsonify({'error': 'That start time has already passed'}), 400

        table_uid = data.get('tableUid')
        # An in-progress booking still occupies its table.
        clash = next((b for b in Booking.query.filter(
            Booking.table_uid == table_uid,
            Booking.status.in_(['booked', 'active'])).all()
            if b.start_time < end and start < b.end_time), None)
        if clash:
            return jsonify({
                'error': f'Already booked {clash.start_time.strftime("%-I:%M %p")}'
                         f'-{clash.end_time.strftime("%-I:%M %p")} for {clash.guest_name}'
            }), 409

        _btable = PoolTable.query.filter_by(uid=table_uid).first()
        b = Booking(
            branch_id=(_btable.branch_id if _btable else selected_branch_id()),
            table_uid=table_uid,
            table_type=data['tableType'],
            table_number=data.get('tableNumber'),
            guest_name=data['guestName'].strip(),
            phone=data.get('phone', '').strip(),
            start_time=start,
            end_time=end,
            code=generate_booking_code(),
        )
        db.session.add(b)
        db.session.commit()
        return jsonify({'success': True, 'id': b.id, 'code': b.code})

    # GET: active (non-cancelled) bookings, soonest first
    rows = (Booking.query
            .filter(Booking.status.in_(['booked', 'active']))
            .filter(_branch_report_scope(Booking))
            .order_by(Booking.start_time).all())
    return jsonify({'bookings': [{
        'id': b.id, 'code': b.code, 'tableUid': b.table_uid, 'tableType': b.table_type,
        'tableNumber': b.table_number, 'guestName': b.guest_name, 'phone': b.phone,
        'startTime': b.start_time.isoformat(),
        'endTime': b.end_time.isoformat() if b.end_time else None,
        'status': b.status,
    } for b in rows]})


@app.route('/api/bookings/<int:booking_id>', methods=['DELETE', 'POST'])
def manage_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)
    if request.method == "DELETE" :
        require_capability('floor') 

        b.status = 'cancelled'
        b.deleted_at = datetime.now()
        b.deleted_by = _actor()   

        target_url = f"{os.environ.get('CENTRAL_URL')}/api/customer/bookings/sync/{b.sync_id}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.delete(target_url)

                if res.status_code not in (200, 201):
                    # Parse error message from the remote node
                    if res.headers.get("content-type") == "application/json":
                        err_msg = res.json().get("error", res.text)
                    else:
                        err_msg = res.text
                        
                    # Flask approach: Return a JSON response with the remote status code
                    return jsonify({
                        "error": f"Local booking not cancelled because remote node rejected request: {err_msg}"
                    }), res.status_code

        except httpx.RequestError as e:
            # Flask approach: Return a 502 Bad Gateway response for connection errors
            return jsonify({
                "error": f"Local booking not cancelled because remote node was unreachable: {str(e)}"
            }), 502

    elif request.method == "POST":
        require_capability('floor')
        # Started, not finished. It leaves the dashboard strip but stays visible
        # to the guest as 'active' until the session is stopped and billed.
        
        b.status = 'active'
        table = PoolTable.query.filter_by(uid=b.table_uid).first()
        if table and table.session_id:
            b.session_id = table.session_id
            # Attribute the tab to the guest so it shows in their game history.
            session = PlaySession.query.get(table.session_id)
            if session and b.customer_id:
                session.customer_id = b.customer_id
                _sp = SessionPlayer.query.filter_by(session_id=session.id).first()
                if _sp and not _sp.customer_id:
                    _sp.customer_id = b.customer_id
        else:
            # The client may mark the booking started before (or without) the
            # table actually being started. Leaving status='active' with no
            # session would strand the booking as "In progress" forever and keep
            # the table blocked, so it stays 'booked' until there is a session
            # to attach it to.
            b.status = 'booked'
            b.session_id = None
        target_url = f"{os.environ.get('CENTRAL_URL')}/api/customer/bookings/sync/{b.sync_id}/active"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(target_url)

                if res.status_code not in (200, 201):
                    # Parse error message from the remote node
                    if res.headers.get("content-type") == "application/json":
                        err_msg = res.json().get("error", res.text)
                    else:
                        err_msg = res.text
                        
                    # Flask approach: Return a JSON response with the remote status code
                    return jsonify({
                        "error": f"Local booking not started because remote node rejected request: {err_msg}"
                    }), res.status_code

        except httpx.RequestError as e:
            # Flask approach: Return a 502 Bad Gateway response for connection errors
            return jsonify({
                "error": f"Local booking not started because remote node was unreachable: {str(e)}"
            }), 502
    db.session.commit()
    return jsonify({'success': True})
        

@app.route('/api/rates', methods=['POST'])
def update_rates():
    require_role('manager')
    data = request.json or {}
    for table_type, vals in data.items():
        row = GlobalRate.query.filter_by(table_type=table_type).first()
        if not row:
            row = GlobalRate(table_type=table_type, weekday_rate=0, weekend_rate=0)
            db.session.add(row)
        if 'weekday' in vals:
            row.weekday_rate = int(vals['weekday'])
        if 'weekend' in vals:
            row.weekend_rate = int(vals['weekend'])
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/tables/<uid>/elapsed', methods=['GET'])
def get_elapsed(uid):
    """Total time on the tab — earlier segments included, not just the current one."""
    require_capability('floor')
    table = PoolTable.query.filter_by(uid=uid).first_or_404()
    banked = prior_seconds(table.session_id)
    if not table.is_active or not table.start_time:
        return jsonify({'elapsedSeconds': banked, 'priorSeconds': banked, 'currentSeconds': 0})
    current = int((datetime.now(timezone.utc) - table.start_time.replace(tzinfo=timezone.utc)).total_seconds())
    current = max(0, current)
    return jsonify({
        'elapsedSeconds': banked + current,
        'priorSeconds': banked,
        'currentSeconds': current,
    })

@app.route('/api/tables/summary', methods=['GET'])
def table_summary ():
    require_capability('floor')
    tables = PoolTable.query.all()
    queue = Queue.query.filter_by(deleted_at=None).all()
    summary = {}

    for table in tables:
        summary[table.table_type]["total"] += 1
        if table.is_active:
            summary[table.table_type]['occupied'] += 1
        else:
            summary[table.table_type]['free'] += 1
    for q in queue:
        summary[q.table_type]['queueCount'] += 1
    return jsonify(summary)

@app.route('/api/logs', methods=['GET', 'POST'])
def handle_logs():
    if request.method == 'POST':
        require_capability('floor')
        data = request.json
        db.session.add(ActivityLog(
            branch_id=selected_branch_id(),
            receipt_id=data['receiptId'], 
            date_string=data['date'], 
            lounge=data['lounge'],
            table_type=data['tableType'], 
            table_id=data['tableId'], 
            served_by = _current_username(),
            player=data['player'], 
            elapsed=data['elapsed'], 
            billable_mins=data['billableMins'], 
            rate=data['rate'], 
            total_cost=data['totalCost']
        ))
        db.session.commit()
        return jsonify({'success': True})

    require_role('manager')
    _a = request.args
    q = ActivityLog.query.filter(_branch_report_scope(ActivityLog))
    if _a.get('receiptId'):
        q = q.filter(ActivityLog.receipt_id.cast(db.String).ilike(f"%{_a['receiptId']}%"))
    if _a.get('player'):
        q = q.filter(ActivityLog.player.ilike(f"%{_a['player']}%"))
    if _a.get('tableType'):
        q = q.filter(ActivityLog.table_type == _a['tableType'])
    if _a.get('tableId'):
        q = q.filter(ActivityLog.table_id == str(_a['tableId']))
    if _a.get('minCost'):
        try: q = q.filter(ActivityLog.total_cost >= int(float(_a['minCost'])))
        except ValueError: pass
    if _a.get('maxCost'):
        try: q = q.filter(ActivityLog.total_cost <= int(float(_a['maxCost'])))
        except ValueError: pass
    if _a.get('dateFrom'):
        try: q = q.filter(ActivityLog.created_at >= datetime.strptime(_a['dateFrom'], '%Y-%m-%d'))
        except ValueError: pass
    if _a.get('dateTo'):
        try: q = q.filter(ActivityLog.created_at < datetime.strptime(_a['dateTo'], '%Y-%m-%d') + timedelta(days=1))
        except ValueError: pass

    # Totals over the WHOLE filtered set (so the footer stays exact even when a
    # single page is returned) — computed by SQL, not by loading every row.
    gross_total = int(q.with_entities(func.coalesce(func.sum(ActivityLog.total_cost), 0)).scalar() or 0)
    total_count = q.count()

    # Opt-in pagination: /api/logs?page=N returns only that page (50 by default).
    # Without ?page the full set is returned (Insights + the dashboard modal,
    # which need every row for analytics, are unaffected).
    _page = _a.get('page')
    if _page:
        try: page_n = max(1, int(_page))
        except ValueError: page_n = 1
        try: per = min(200, max(1, int(_a.get('perPage', 50))))
        except ValueError: per = 50
        logs = q.order_by(ActivityLog.id.desc()).offset((page_n - 1) * per).limit(per).all()
    else:
        page_n, per = 1, (total_count or 1)
        logs = q.order_by(ActivityLog.id.desc()).all()

    # ── member attribution ──────────────────────────────────────────────────
    # Who a session belongs to, for analytics, comes from the normalized roster
    # (SessionPlayer) — one row per player, each carrying its own optional
    # customer_id — NOT from the single owner id on the ledger row, which can
    # only ever name one person. A tab with three members yields three member
    # entries here; walk-in names carry no customer_id and are left out, because
    # only accounts are counted. Resolved in two bulk queries, not one per log.
    session_ids = [l.session_id for l in logs if l.session_id]
    roster_by_session = {}
    if session_ids:
        for sp in (SessionPlayer.query
                   .filter(SessionPlayer.session_id.in_(session_ids)).all()):
            roster_by_session.setdefault(sp.session_id, []).append(sp)

    member_ids = {sp.customer_id for rows in roster_by_session.values()
                  for sp in rows if sp.customer_id}
    member_ids.update(l.customer_id for l in logs if l.customer_id)
    member_names = {}
    if member_ids:
        for c in Customer.query.filter(Customer.id.in_(member_ids)).all():
            member_names[c.id] = c.name

    def members_for(l):
        """The linked accounts on this session — the unit analytics counts."""
        roster = roster_by_session.get(l.session_id, [])
        members = [{'customerId': sp.customer_id,
                    'name': member_names.get(sp.customer_id, sp.name)}
                   for sp in roster if sp.customer_id]
        # Sessions billed before the roster table existed have no rows, but may
        # still carry a single owner id on the ledger — keep attributing those.
        if not members and l.customer_id:
            members.append({'customerId': l.customer_id,
                            'name': member_names.get(l.customer_id, l.player)})
        return members

    def player_count(l):
        """Total people on the tab, so a per-head split has a denominator.

        Prefers the roster; on old rows with none, counts the comma-joined
        cosmetic name so an even split still behaves on historical data.
        """
        roster = roster_by_session.get(l.session_id, [])
        if roster:
            return len(roster)
        name = (l.player or '').strip()
        if not name or name.lower() == 'walk-in guest':
            return 1
        return max(1, len([p for p in name.split(',') if p.strip()]))

    return jsonify({
        'logs': [{
            'receiptId': l.receipt_id, 
            'date': l.date_string, 
            'lounge': l.lounge,
            'tableType': l.table_type, 
            'tableId': l.table_id, 
            'player': l.player, 
            # The linked accounts on this session and the head count, so
            # analytics can credit members individually instead of treating the
            # comma-joined name as one guest.
            'members': members_for(l),
            'playerCount': player_count(l),
            'elapsed': l.elapsed, 
            'billableMins': l.billable_mins, 
            'rate': l.rate, 
            # Table time only — canteen orders on the same tab are their own
            # rows, joined by billGroup.
            'totalCost': l.total_cost,
            'segments': parse_segments(l.segments_json),
            # Without these a bill reopened from the log loses its food lines
            # and shows a total that doesn't match its own itemisation.
            'canteenItems': parse_segments(l.canteen_json),
            'playTotal': l.play_total if l.play_total is not None else l.total_cost,
            'canteenTotal': l.canteen_total or 0,
            'splitCount': l.split_count or 1,
            'paymentStatus': l.payment_status,
            'paymentMethod': l.payment_method or '',
            'billGroup': l.bill_group,
            'khataName': l.khata_name,
            'logId': l.id,
            'payUrl': (ensure_pay_link(
                amount=l.total_cost, kind='session', reference=str(l.receipt_id),
                payer_name=l.player or '', log_id=l.id,
            ) if l.payment_status != 'paid' else None),
        } for l in logs],
        'grossTotal': gross_total,
        'total': total_count,
        'page': page_n,
        'perPage': per,
    })

@app.route('/api/tables/reorder', methods=['POST'])
def reorder_tables():
    require_capability('floor')
    order = request.json.get('order', [])
    for i, uid in enumerate(order):
        PoolTable.query.filter_by(uid=uid).update({'sort_order': i})
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/lounges/<lounge_ref>', methods=['POST', 'DELETE'])
def modify_lounge(lounge_ref):
    require_role('manager')
    # Lounges are identified by their string `uid`; also accept a numeric id.
    # get_or_404 can't be used here — it looks up by primary key (id), not uid,
    # so passing a uid string silently matched the wrong row (or nothing).
    lounge = Lounge.query.filter_by(uid=lounge_ref).first()
    if lounge is None and lounge_ref.isdigit():
        lounge = Lounge.query.get(int(lounge_ref))
    if lounge is None:
        abort(404)
    if request.method == 'DELETE':
        # Tables reference the lounge by uid, and only live (non-deleted) tables
        # should block removal. The old guard compared against the id, never
        # matched, and so let a lounge with tables be deleted — orphaning them.
        live_tables = (PoolTable.query
                       .filter_by(lounge_uid=lounge.uid)
                       .filter(PoolTable.status != 'deleted').count())
        if live_tables > 0:
            return jsonify({'error': 'Lounge still has tables'}), 400
        lounge.status = 'deleted'
        lounge.deleted_at = datetime.now()
        lounge.deleted_by = _actor()
        db.session.commit()
        return jsonify({'success': True})
    # POST = rename
    lounge.name = (request.json.get('name', lounge.name) or lounge.name).strip() or lounge.name
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/lounges', methods=['POST'])
def add_lounge():
    require_role('manager')
    lounge = Lounge(name=request.json.get('name', 'New Lounge').strip(), uid=f"lounge-{int(time.time()*1000)}", status='active', branch_id=selected_branch_id())
    db.session.add(lounge)
    db.session.commit()
    return jsonify({'success': True, 'id': lounge.uid, 'name': lounge.name})

@app.route('/staff', defaults={'path': ''})
@app.route('/staff/<path:path>')
def staff_spa(path):
    """The staff app: a SEPARATE build artifact, reachable only under /staff.

    A guest at / never receives it — no dashboard components, no staff route
    table, no till endpoints listed in their JavaScript.
    """
    if not SERVE_STAFF:
        abort(404)
    return send_from_directory(DIST_DIR, 'staff.html')

WEBHOOK_SECRET = os.getenv('EASYPAISA_WEBHOOK_SECRET', 'your_shared_secret_key')

@app.route('/webhooks/easypaisa', methods=['POST'])
def easypaisa_webhook():
    # 1. Grab the raw payload data and the signature header
    # We use get_data() because signatures require the raw, exact bytes sent.
    payload_bytes = request.get_data()
    received_signature = request.headers.get('X-Signature') # Check provider docs for the exact header name
    
    if not received_signature:
        return jsonify({"error": "Missing signature header"}), 400

    # 2. Security Check: Verify the signature
    computed_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(received_signature, computed_signature):
        # Log this securely; do not process the transaction
        app.logger.warning("Unauthorized webhook payload detected!")
        return jsonify({"error": "Invalid signature verification"}), 401

    # 3. Safely parse the verified JSON data
    try:
        data = json.loads(payload_bytes)
    except json.JSONDecodeError:
        return jsonify({"error": "Malformed JSON payload"}), 400

    order_id = data.get('orderId')
    payment_status = data.get('status') # Usually 'succeeded', 'PAID', or 'SUCCESS'

    # 4. Handle Idempotency (Prevent duplicate processing)
    # TODO: Check your database first to see if this order_id is already marked 'Paid'
    # if is_order_already_processed(order_id):
    #     return jsonify({"status": "already processed"}), 200

    # 5. Process the payment logic
    if payment_status == 'succeeded':
        # TODO: Mark order as paid in your database, dispatch goods, or unlock features
        print(f"Payment received successfully for Order ID: {order_id}")
    else:
        # TODO: Mark order as failed or cancelled
        print(f"Payment failed for Order ID: {order_id}")

    # 6. Return an immediate HTTP 200 OK so the provider stops retrying
    return jsonify({"status": "success"}), 200


@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def api_not_found(path):
    """Unknown API route.

    Without this, the GET-only SPA catch-all answers unregistered POSTs with a
    405 HTML page, which reads like a broken button rather than a missing
    endpoint. Werkzeug prefers the more specific rules above, so real routes are
    unaffected.
    """
    return jsonify({'error': f'Unknown API endpoint: /api/{path}'}), 404


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def customer_spa(path):
    """Everything that isn't /staff or /api is the customer portal."""
    if path.startswith(('api/', 'staff', 'staff/')):
        abort(404)
    candidate = os.path.join(DIST_DIR, path)
    if path and os.path.isfile(candidate):
        return send_from_directory(DIST_DIR, path)
    # On a staff-only box there is no public portal at all; hand back the staff
    # shell so the LAN tablets still work from the bare host name.
    if not SERVE_CUSTOMER:
        return send_from_directory(DIST_DIR, 'staff.html')
    return send_from_directory(DIST_DIR, 'index.html')



DEFAULT_TABLE_TYPES = [
    {'key': 'snooker',        'label': 'Snooker',        'color': '#34d399', 'renderer': 'pool',        'badge': 'S',   'sort': 1},
    {'key': 'pool',           'label': '8-Ball Pool',    'color': '#38bdf8', 'renderer': 'pool',        'badge': '8',   'sort': 2},
    {'key': 'privateSnooker', 'label': 'VIP Snooker',    'color': '#fbbf24', 'renderer': 'pool',        'badge': 'VS',  'sort': 3},
    {'key': 'privatePool',    'label': 'VIP Pool',       'color': '#c084fc', 'renderer': 'pool',        'badge': 'VP',  'sort': 4},
    {'key': 'ps5',            'label': 'PlayStation 5',  'color': '#3b82f6', 'renderer': 'playstation', 'badge': 'P5',  'sort': 5},
    {'key': 'ps4',            'label': 'PlayStation 4',  'color': '#60a5fa', 'renderer': 'playstation', 'badge': 'P4',  'sort': 6},
    {'key': 'xboxx',          'label': 'Xbox Series X',  'color': '#22c55e', 'renderer': 'xbox',        'badge': 'X1',  'sort': 7},
    {'key': 'xbox1',          'label': 'Xbox One',       'color': '#22c55e', 'renderer': 'xbox',        'badge': 'XB',  'sort': 8},
    {'key': 'pc',              'label': 'PC',        'color': '#AB47BC', 'renderer': 'pc',        'badge': 'PC',  'sort': 9},
    {'key': 'foosball',       'label': 'Foosball',       'color': '#a3e635', 'renderer': 'foosball',    'badge': 'FB',  'sort': 10},
]


def _sample_table(key):
    """A standard, inactive display table used to preview a type's card.
    Only the fields PoolTable.vue actually reads for a display table."""
    return {'uid': f'sample-{key}', 'id': '1', 'type': key,
            'isActive': False, 'bookingName': '', 'players': [], 'resumable': False}


def seed_table_types():
    """Seed the type registry (and a 0-rate row per type) without touching rows
    that already exist — so custom colours/rates survive restarts."""
    for t in DEFAULT_TABLE_TYPES:
        row = TableType.query.filter_by(key=t['key']).first()
        if row is None:
            row = TableType(key=t['key'], label=t['label'], color=t['color'],
                            renderer=t['renderer'], badge=t['badge'], sort_order=t['sort'])
            db.session.add(row)
        if row.sample_object is None:              # seed/backfill without clobbering edits
            row.sample_object = _sample_table(t['key'])
        if not GlobalRate.query.filter_by(table_type=t['key']).first():
            db.session.add(GlobalRate(table_type=t['key'], weekday_rate=0, weekend_rate=0))
    print("Seeded: default tableTypes")
    db.session.commit()


def seed_rates():
    """Ensure every known type has a rate row; never overwrites existing rows."""
    for table_type, vals in DEFAULT_RATES.items():
        if not GlobalRate.query.filter_by(table_type=table_type).first():
            db.session.add(GlobalRate(table_type=table_type,
                                      weekday_rate=vals['weekday'],
                                      weekend_rate=vals['weekend']))
    db.session.commit()

def seed_default_owner():
            if User.query.count() == 0:
                owner = User(username='owner', role='owner')
                owner.set_password('change-me-now')
                db.session.add(owner)
                db.session.commit()
                print('⚠️  Created default account  owner / change-me-now  — LOG IN AND CHANGE IT.')

# --- MIGRATION ---

# Neutral column kinds, mapped to Postgres DDL types.
COLUMN_TYPES = {
    'postgresql': {'datetime': 'TIMESTAMP', 'text': 'TEXT', 'int': 'INTEGER', 'bool': 'BOOLEAN'},
}


def run_migrations():
    """Apply incremental schema changes to an existing database.

    db.create_all() adds new tables but never alters existing ones, so columns
    introduced after a deployment have to be added by hand. Safe to re-run on Postgres.

    Two things this has to get right that a naive version doesn't:

    1. Postgres aborts the WHOLE transaction when a statement fails, so each
       column is added and committed on its own. One unexpected failure then
       costs one column instead of every migration after it.
    2. Both engines backfill a DEFAULT into existing rows, so a freshly added
       `payment_status DEFAULT 'pending'` would silently mark every historical
       bill as owed. Rows that predate a column are corrected at the moment the
       column is created, which is the only time they can be identified.
    """
    dialect = db.engine.name
    types = COLUMN_TYPES.get(dialect, COLUMN_TYPES['postgresql'])

    inspector = sa_inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    columns_by_table = {
        table: {c['name'] for c in inspector.get_columns(table)}
        for table in existing_tables
    }

    def add_column(table, column, kind, *, default=None, length=None):
        """Add one column if it's missing. Returns True if it was just created."""
        if table not in existing_tables:
            return False           # create_all() made it with the column present
        if column in columns_by_table.get(table, set()):
            return False

        if kind == 'str':
            sql_type = f'VARCHAR({length or 255})'
        else:
            sql_type = types[kind]

        # Quote identifiers: `user` is a reserved word in Postgres, so an
        # unquoted `ALTER TABLE user` silently failed there — which is why the
        # capabilities column and the canteen_manager backfill never reached
        # production. Double quotes are valid identifiers on Postgres.
        ddl = f'ALTER TABLE "{table}" ADD COLUMN "{column}" {sql_type}'
        if default is not None:
            # Quoted literal: correct for both engines, and avoids a bare value
            # being read as an identifier.
            ddl += f" DEFAULT '{default}'" if isinstance(default, str) else f' DEFAULT {default}'

        try:
            db.session.execute(sa_text(ddl))
            db.session.commit()
        except Exception as exc:                              # noqa: BLE001
            # Roll back so Postgres doesn't refuse everything that follows.
            db.session.rollback()
            print(f'  migration skipped: {table}.{column} ({exc.__class__.__name__})')
            return False

        columns_by_table.setdefault(table, set()).add(column)
        print(f'  migrated: {table}.{column}')
        return True

    def backfill(table, column, value, condition=''):
        """Set a value on rows that existed before the column did."""
        where = f' WHERE {condition}' if condition else ''
        try:
            result = db.session.execute(
                sa_text(f'UPDATE "{table}" SET "{column}" = :value{where}'), {'value': value}
            )
            db.session.commit()
            if result.rowcount:
                print(f'  backfilled: {result.rowcount} row(s) in {table}.{column}')
        except Exception as exc:                              # noqa: BLE001
            db.session.rollback()
            print(f'  backfill skipped: {table}.{column} ({exc.__class__.__name__})')

    add_column('pool_table', 'session_id', 'int')
    add_column('pool_table', 'status', 'str', length=50)
    add_column('activity_log', 'session_id', 'int')
    add_column('activity_log', 'segments_json', 'text')
    add_column('activity_log', 'served_by', 'text')
    add_column('booking', 'end_time', 'datetime')
    add_column('booking', 'customer_id', 'int')
    add_column('booking', 'session_id', 'int')
    add_column('play_session', 'customer_id', 'int')

    # Bills that predate payment tracking were all taken at the counter under
    # the old flow. The DEFAULT marks them 'pending', which would invent debts
    # that never existed — so they're corrected here, on creation only.
    if add_column('activity_log', 'payment_status', 'str', length=20, default='pending'):
        backfill('activity_log', 'payment_status', 'paid')
    add_column('activity_log', 'settled_at', 'datetime')
    add_column('activity_log', 'khata_name', 'str', length=100)
    add_column('activity_log', 'customer_id', 'int')

    if add_column('canteen_order', 'payment_status', 'str', length=20, default='pending'):
        backfill('canteen_order', 'payment_status', 'paid')
    add_column('canteen_order', 'settled_at', 'datetime')
    add_column('canteen_order', 'khata_name', 'str', length=100)

    add_column('activity_log', 'canteen_json', 'text')
    add_column('activity_log', 'play_total', 'int')
    add_column('activity_log', 'canteen_total', 'int')
    add_column('activity_log', 'split_count', 'int')
    add_column('activity_log', 'payment_method', 'str', length=20, default='')
    add_column('activity_log', 'bill_group', 'str', length=40)
    add_column('canteen_order', 'bill_group', 'str', length=40)
    add_column('activity_log', 'closed_at', 'datetime')
    add_column('activity_log', 'closed_by', 'str', length=80)
    add_column('canteen_order', 'closed_at', 'datetime')
    add_column('canteen_order', 'closed_by', 'str', length=80)
    add_column('user', 'capabilities', 'str', length=120, default='floor')

    # The canteen_manager role is gone: it's a receptionist whose one counter is
    # the canteen. Run unconditionally, not only when the column is created —
    # an account can be written by an older build after the migration has
    # already added the column, and it would otherwise keep the wrong counter.
    backfill('user', 'capabilities', 'canteen', "role = 'canteen_manager'")
    backfill('user', 'role', 'receptionist', "role = 'canteen_manager'")

    # Nobody should be left with no counter at all — they could sign in and
    # find every page closed to them.
    backfill('user', 'capabilities', 'floor',
             "(capabilities IS NULL OR capabilities = '') AND role = 'receptionist'")
    add_column('canteen_product', 'img_url', 'str', length=255)
    add_column('activity_log', 'created_at', 'datetime')

    # NOTE: the historical-bill correction now happens in the backfill above,
    # at the moment the column is added. Checking for NULL here never worked:
    # both engines populate the DEFAULT into existing rows, so there was
    # nothing NULL left to find.

    # Bookings marked 'active' whose session is already settled (or that never
    # had one) are stranded: they read as "In progress" forever and block their
    # station from being booked. Release them on startup so existing databases
    # recover without anyone having to find each stuck table by hand.
    stranded = []
    for booking in Booking.query.filter(Booking.status == 'active').all():
        session = PlaySession.query.get(booking.session_id) if booking.session_id else None
        table = PoolTable.query.filter_by(uid=booking.table_uid).first()
        session_live = bool(session) and session.status != 'settled'
        table_live = bool(table) and table.session_id == booking.session_id and booking.session_id
        if not session_live and not table_live:
            booking.status = 'completed'
            stranded.append(booking.id)
    if stranded:
        db.session.commit()
        print(f'  migrated: released {len(stranded)} stranded in-progress booking(s)')

    # 'fulfilled' predates the active/completed split: those bookings were
    # started AND finished under the old flow, so they are completed.
    legacy = Booking.query.filter_by(status='fulfilled').all()
    if legacy:
        for booking in legacy:
            booking.status = 'completed'
        db.session.commit()
        print(f'  migrated: {len(legacy)} booking(s) fulfilled -> completed')

    # ALTER TABLE leaves pre-existing rows with a NULL end_time, and a booking
    # with no end can't be checked for clashes — the whole day has to be treated
    # as blocked. Give those rows the minimum length so the calendar is usable
    # again; anything longer has to be re-entered by hand.
    orphans = Booking.query.filter(Booking.end_time.is_(None)).all()
    if orphans:
        for booking in orphans:
            booking.end_time = booking.start_time + timedelta(minutes=MIN_BOOKING_MINUTES)
        db.session.commit()
        print(f'  migrated: {len(orphans)} booking(s) had no end time — '
              f'assumed {MIN_BOOKING_MINUTES} minutes. Check any that are still upcoming.')


def run_seeds():
    """Idempotent first-run data: rate rows, a default owner, the canteen menu.

    Safe to run on every deploy — each seed checks for existing rows before
    inserting. Kept separate from schema so it can run after `flask db upgrade`
    rather than being tangled up with table creation.
    """
    seed_rates()
    seed_table_types()
    seed_default_owner()
    if SERVE_STAFF:
        seed_canteen()


@app.cli.command('seed')
def seed_command():
    """Populate first-run data (rates, default owner, canteen menu)."""
    run_seeds()
    print('✓ seed complete')


@app.cli.command('sync-legacy-schema')
def sync_legacy_schema_command():
    """ONE-TIME bridge for a database created before Alembic.

    Runs the old idempotent ALTER-based migrator and its data repairs to bring
    a drifted database (e.g. a production Postgres that never received the
    last few pre-Alembic migrations) up to the current schema. After running
    this once, `flask db stamp head` marks the database as managed by Alembic,
    and this command should never be needed again.
    """
    # create_all adds any base table this DB never had (a no-op on tables that
    # already exist); run_migrations then adds the missing columns and applies
    # the data repairs, bringing a pre-Alembic Postgres database up to date.
    db.create_all()
    run_migrations()
    print('✓ legacy schema sync complete — now run:  flask db stamp head')


# --- RUN PRODUCTION SERVER ---
if __name__ == '__main__':
    from flask_migrate import upgrade as alembic_upgrade

    port = int(os.environ.get('PORT', 5000))
    # Either form works:  python index.py --dev   |   DEV=1 python index.py
    dev = ('--dev' in sys.argv
           or os.environ.get('DEV', '').lower() in ('1', 'true', 'yes', 'on'))

    # The reloader runs this file in TWO processes: a supervisor that watches for
    # changes, and the worker that actually serves. Only the worker should touch
    # the database, or migrations run twice on every save.
    reloader_supervisor = dev and not os.environ.get('WERKZEUG_RUN_MAIN')

    # In a container or on Render the entrypoint/pre-deploy step runs
    # `flask db upgrade` and `flask seed` itself and sets MIGRATE_ON_START=0,
    # so the server process just serves. Everywhere else this defaults on, so
    # `python index.py` stays a one-command dev start that brings the schema up
    # and seeds before serving.
    bootstrap = (not reloader_supervisor) and \
        os.environ.get('MIGRATE_ON_START', '1').lower() in ('1', 'true', 'yes', 'on')

    if bootstrap:
        with app.app_context():
            # Apply Alembic migrations, then seed. This replaces the old
            # create_all() + run_migrations() so local dev uses the exact same
            # migration path as production — no more per-dialect DDL to keep in
            # step.
            alembic_upgrade()
            run_seeds()
            if IS_CLOUD:
                try:
                    enable_rls(db)   # DB-enforced tenant isolation (idempotent)
                    print('[tenancy] RLS enabled on tenant tables')
                except Exception as _e:
                    print(f'[tenancy] RLS enable skipped: {_e}')

    if dev:
        if not reloader_supervisor:
            print(f"🔁 Dev server: auto-reload on, port {port}")
        # use_debugger stays OFF on purpose: Werkzeug's interactive debugger can
        # execute arbitrary code from the browser, and this binds to 0.0.0.0 so
        # tablets on the LAN can reach it.
        app.run(host='0.0.0.0', port=port, debug=True,
                use_reloader=True, use_debugger=False)
    else:
        print("🚀 Starting Production Server...")
        serve(app, host='0.0.0.0', port=port)