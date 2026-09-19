"""Customer-facing API — isolated from the staff application.

Isolation is enforced at three levels, and all three matter:

  1. IDENTITY   Customers live in their own table with no role column. There is
                no value a customer row can hold that grants staff access.
  2. TOKENS     Customer tokens are signed with a DIFFERENT key and carry
                aud="customer". A staff endpoint can't merely reject one — it
                can't verify the signature at all. The reverse holds too.
  3. SURFACE    Everything here is a blueprint under /api/customer. No staff
                route is reachable through it, and it can be deployed on its
                own (APP_ROLE=customer) without the staff app present.

Nothing in this file may import a staff handler or read a staff model beyond
what a customer legitimately owns.
"""

import json
import os
import re
import smtplib
import time
import hmac
import secrets
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, jsonify, request, g
from werkzeug.security import generate_password_hash, check_password_hash

from models import (db, Customer, PasswordResetCode, Booking, PoolTable, Lounge,
                    PlaySession, SessionPlayer, ActivityLog, CanteenOrder, GlobalRate,
                    Branch, generate_booking_code)

customer_bp = Blueprint('customer', __name__, url_prefix='/api/customer')

# Injected by index.py once it has defined the helper — importing it directly
# would be circular.
_pay_link = None


def set_pay_link(fn):
    global _pay_link
    _pay_link = fn

# ── configuration ───────────────────────────────────────────────────────────

# Separate from the staff JWT key ON PURPOSE. If these are ever the same value,
# the audience claim is the only thing standing between a customer and the till.
CUSTOMER_JWT_SECRET = os.environ.get('CUSTOMER_JWT_SECRET') or 'dev-only-customer-secret-change-me'
CUSTOMER_AUDIENCE = 'customer'
RESET_AUDIENCE = 'customer-reset'

ACCESS_TOKEN_DAYS = 30
RESET_CODE_TTL_MINUTES = 10
MAX_CODE_ATTEMPTS = 5

APP_NAME = os.environ.get('APP_NAME', 'Baize')


# ── phone normalisation (mirror of frontend/src/utils/phone.js) ─────────────

def normalise_phone(raw):
    """Every spelling of a Pakistani mobile collapses to '+92XXXXXXXXXX'.

    Doing this only on the client would be cosmetic: one direct API call with
    '0300-1234567' would create a second account for a number that already
    exists as '+923001234567'. The unique index depends on this running here.
    """
    digits = re.sub(r'\D', '', str(raw or ''))
    if digits.startswith('0092'):
        digits = digits[4:]
    elif digits.startswith('92') and len(digits) > 10:
        digits = digits[2:]
    digits = digits.lstrip('0')
    # Reject rather than truncate: an extra digit must not silently become
    # somebody else's number.
    if not re.fullmatch(r'3\d{9}', digits):
        return None
    return f'+92{digits}'


EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')


def valid_email(raw):
    return bool(raw) and bool(EMAIL_RE.fullmatch(str(raw).strip()))


# ── rate limiting ───────────────────────────────────────────────────────────
# In-process and therefore per-worker. Adequate for a single waitress instance;
# move to Redis if this is ever deployed behind more than one process.

_hits = {}


def _throttle(key, limit, window_seconds):
    """True when the caller is over budget."""
    now = time.time()
    window_start = now - window_seconds
    stamps = [t for t in _hits.get(key, []) if t > window_start]
    stamps.append(now)
    _hits[key] = stamps
    # Opportunistic cleanup so this dict can't grow without bound
    if len(_hits) > 5000:
        for k in [k for k, v in _hits.items() if not v or max(v) < window_start]:
            _hits.pop(k, None)
    return len(stamps) > limit


def _client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    return forwarded.split(',')[0].strip() if forwarded else (request.remote_addr or 'unknown')


def rate_limit(limit, window_seconds, scope='ip'):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = f'{fn.__name__}:{scope}:{_client_ip()}'
            if _throttle(key, limit, window_seconds):
                return jsonify({'error': 'Too many attempts. Please wait a few minutes.'}), 429
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ── tokens ──────────────────────────────────────────────────────────────────

def issue_customer_token(customer):
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(customer.id),
        'aud': CUSTOMER_AUDIENCE,
        'iat': now,
        'exp': now + timedelta(days=ACCESS_TOKEN_DAYS),
    }
    return jwt.encode(payload, CUSTOMER_JWT_SECRET, algorithm='HS256')


def _password_fingerprint(customer):
    """Short digest of the current password hash.

    Embedding this in the reset token makes the token single-use without any
    server-side state: the moment the password changes the fingerprint changes,
    and the token that performed the change stops verifying.
    """
    return hmac.new(
        CUSTOMER_JWT_SECRET.encode(),
        (customer.password_hash or '').encode(),
        'sha256',
    ).hexdigest()[:16]


def issue_reset_token(customer):
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(customer.id),
        'aud': RESET_AUDIENCE,   # cannot be used as an access token
        'pwf': _password_fingerprint(customer),
        'iat': now,
        'exp': now + timedelta(minutes=RESET_CODE_TTL_MINUTES),
    }
    return jwt.encode(payload, CUSTOMER_JWT_SECRET, algorithm='HS256')


def _decode(token, audience):
    return jwt.decode(token, CUSTOMER_JWT_SECRET, algorithms=['HS256'], audience=audience)


def require_customer(fn):
    """Guard for customer-owned resources.

    Note what this does NOT do: consult a role. There is no role to consult —
    which is exactly the point.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            return jsonify({'error': 'Sign in to continue'}), 401
        try:
            claims = _decode(header[7:], CUSTOMER_AUDIENCE)
        except jwt.PyJWTError:
            return jsonify({'error': 'Session expired'}), 401

        customer = db.session.get(Customer, int(claims['sub']))
        if not customer or not customer.is_active:
            return jsonify({'error': 'Session expired'}), 401
        g.customer = customer
        return fn(*args, **kwargs)
    return wrapper


def customer_json(customer):
    """Only ever the caller's own fields. No club data, no staff data."""
    return {'name': customer.name, 'phone': customer.phone, 'email': customer.email}


# ── email delivery ──────────────────────────────────────────────────────────

def send_email(to_address, subject, body):
    """Send via SMTP when configured; otherwise log and carry on.

    Never raises. A mail outage must not turn into a 500 that tells the caller
    whether the account existed.
    """
    host = os.environ.get('SMTP_HOST')
    if not host:
        print(f'[email:not-configured] to={to_address} subject={subject}\n{body}')
        return False

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = os.environ.get('SMTP_FROM', f'no-reply@{host}')
    message['To'] = to_address
    message.set_content(body)

    try:
        port = int(os.environ.get('SMTP_PORT', 587))
        with smtplib.SMTP(host, port, timeout=10) as server:
            if os.environ.get('SMTP_STARTTLS', '1') == '1':
                server.starttls()
            user = os.environ.get('SMTP_USER')
            if user:
                server.login(user, os.environ.get('SMTP_PASSWORD', ''))
            server.send_message(message)
        return True
    except Exception as exc:                      # noqa: BLE001 - deliberately broad
        print(f'[email:failed] to={to_address}: {exc}')
        return False


# ── routes ──────────────────────────────────────────────────────────────────

@customer_bp.route('/register', methods=['POST'])
@rate_limit(limit=5, window_seconds=3600)
def register():
    data = request.json or {}
    phone = normalise_phone(data.get('phone'))
    email = (data.get('email') or '').strip().lower()
    name = (data.get('name') or '').strip()
    password = data.get('password') or ''

    if not phone:
        return jsonify({'error': "That phone number doesn't look right", 'field': 'phone'}), 400
    if not name:
        return jsonify({'error': 'Please enter your name', 'field': 'name'}), 400
    if not valid_email(email):
        return jsonify({'error': 'A valid email is required for verification codes',
                        'field': 'email'}), 400
    if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return jsonify({'error': 'Password needs 8+ characters, a letter and a number',
                        'field': 'password'}), 400

    if Customer.query.filter_by(phone=phone).first():
        return jsonify({'error': 'An account already uses this number', 'field': 'phone'}), 409

    customer = Customer(phone=phone, email=email, name=name)
    customer.set_password(password)
    db.session.add(customer)
    db.session.commit()

    return jsonify({'token': issue_customer_token(customer),
                    'customer': customer_json(customer)}), 201


@customer_bp.route('/login', methods=['POST'])
@rate_limit(limit=10, window_seconds=900)
def login():
    data = request.json or {}
    phone = normalise_phone(data.get('phone'))
    password = data.get('password') or ''

    customer = Customer.query.filter_by(phone=phone).first() if phone else None
    # One message for every failure. Naming which half was wrong would turn this
    # into a way to test which numbers are registered.
    if not customer or not customer.is_active or not customer.check_password(password):
        return jsonify({'error': 'Phone number or password is incorrect'}), 401

    return jsonify({'token': issue_customer_token(customer),
                    'customer': customer_json(customer)})


@customer_bp.route('/password/forgot', methods=['POST'])
@rate_limit(limit=5, window_seconds=900)
def forgot_password():
    """Always answers 202, whatever happens.

    Any difference in status, body or timing between a registered and an
    unregistered number is an account-enumeration oracle.
    """
    data = request.json or {}
    phone = normalise_phone(data.get('phone'))
    customer = Customer.query.filter_by(phone=phone).first() if phone else None

    if customer and customer.is_active:
        # Retire any outstanding codes so only the newest one works
        PasswordResetCode.query.filter_by(customer_id=customer.id, used_at=None).update(
            {'used_at': datetime.now()}
        )
        code = f'{secrets.randbelow(1_000_000):06d}'
        db.session.add(PasswordResetCode(
            customer_id=customer.id,
            code_hash=generate_password_hash(code),
            expires_at=datetime.now() + timedelta(minutes=RESET_CODE_TTL_MINUTES),
        ))
        db.session.commit()
        send_email(
            customer.email,
            f'Your {APP_NAME} verification code',
            f'Hi {customer.name},\n\n'
            f'Your verification code is {code}\n\n'
            f'It expires in {RESET_CODE_TTL_MINUTES} minutes. '
            f'If you did not request this, you can ignore this email.\n',
        )

    return jsonify({'sent': True}), 202


@customer_bp.route('/password/verify', methods=['POST'])
@rate_limit(limit=15, window_seconds=900)
def verify_code():
    data = request.json or {}
    phone = normalise_phone(data.get('phone'))
    code = re.sub(r'\D', '', str(data.get('code') or ''))
    invalid = jsonify({'error': 'That code is not valid or has expired', 'field': 'code'}), 400

    customer = Customer.query.filter_by(phone=phone).first() if phone else None
    if not customer:
        return invalid

    record = (PasswordResetCode.query
              .filter_by(customer_id=customer.id, used_at=None)
              .order_by(PasswordResetCode.id.desc())
              .first())
    if not record or record.expires_at < datetime.now():
        return invalid

    if record.attempts >= MAX_CODE_ATTEMPTS:
        record.used_at = datetime.now()          # burn it rather than allow more guesses
        db.session.commit()
        return invalid

    record.attempts += 1
    if not check_password_hash(record.code_hash, code):
        db.session.commit()
        return invalid

    record.used_at = datetime.now()
    db.session.commit()
    return jsonify({'resetToken': issue_reset_token(customer)})


@customer_bp.route('/password/reset', methods=['POST'])
@rate_limit(limit=10, window_seconds=900)
def reset_password():
    data = request.json or {}
    password = data.get('password') or ''

    try:
        claims = _decode(data.get('resetToken') or '', RESET_AUDIENCE)
    except jwt.PyJWTError:
        return jsonify({'error': 'This reset has expired. Please start again.'}), 400

    if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return jsonify({'error': 'Password needs 8+ characters, a letter and a number',
                        'field': 'password'}), 400

    customer = db.session.get(Customer, int(claims['sub']))
    if not customer:
        return jsonify({'error': 'This reset has expired. Please start again.'}), 400

    # Already spent: the password has changed since this token was issued.
    if not hmac.compare_digest(claims.get('pwf', ''), _password_fingerprint(customer)):
        return jsonify({'error': 'This reset has already been used. Please start again.'}), 400

    customer.set_password(password)
    db.session.commit()
    return jsonify({'ok': True})


@customer_bp.route('/me', methods=['GET'])
@require_customer
def me():
    return jsonify({'customer': customer_json(g.customer)})

# ── booking ─────────────────────────────────────────────────────────────────
#
# What a guest is allowed to know about the club: which stations exist, and
# which time ranges are already taken. NOT who took them, not what anyone is
# paying, not whether a table is currently mid-session and for how much.

MIN_BOOKING_MINUTES = 30


def _parse_date(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


@customer_bp.route('/availability', methods=['GET'])
def availability():
    """Stations plus the busy ranges for one day.

    Deliberately returns intervals with NO identity attached. Sending the other
    guests' names and phone numbers to every signed-in customer would be a data
    leak dressed up as a booking calendar — the staff endpoint does include
    them, which is exactly why this doesn't reuse it.
    """
    day = _parse_date(request.args.get('date')) or datetime.now().date()
    start_of_day = datetime.combine(day, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    # Multi-branch: a customer picks a branch (location); we show only that
    # branch's stations so a booking can't land on another branch's table.
    active_branches = (Branch.query.filter_by(deleted_at=None)
                       .order_by(Branch.sort_order, Branch.id).all())
    sel = request.args.get('branch')
    branch = next((b for b in active_branches if b.uid == sel), None)
    if branch is None and len(active_branches) == 1:
        branch = active_branches[0]              # single-branch clubs need no picker

    def _scoped(q, Model):
        # NULL branch_id (legacy rows) stays visible during rollout.
        return q.filter((Model.branch_id == branch.id) | (Model.branch_id.is_(None))) if branch else q

    # No branch chosen while several exist → show nothing until the customer
    # picks a location (avoids booking a station at the wrong branch).
    if branch is None:
        lounges, tables, bookings = [], [], []
    else:
        lounges = _scoped(Lounge.query.filter(Lounge.status != 'deleted'), Lounge).all()
        tables = _scoped(PoolTable.query.filter(PoolTable.status != 'deleted'), PoolTable).order_by(PoolTable.sort_order).all()
        bookings = _scoped(Booking.query
                           .filter(Booking.status.in_(['booked', 'active']),
                                   Booking.start_time < end_of_day,
                                   Booking.end_time > start_of_day), Booking).all()
    rates = GlobalRate.query.all()
    
    is_weekend = datetime.today().weekday() >= 5

    rate_map = {
        r.table_type: (r.weekend_rate if is_weekend else r.weekday_rate)
        for r in rates
    }

    return jsonify({
        'date': day.isoformat(),
        'branches': [{'uid': b.uid, 'name': b.name} for b in active_branches],
        'selectedBranch': branch.uid if branch else None,
        'lounges': [{'uid': l.uid, 'name': l.name} for l in lounges],
        'tables': [{'uid': t.uid, 'id': t.table_id, 'type': t.table_type,
                    'loungeUid': t.lounge_uid, 'isActive': t.is_active, 'currentRate': rate_map.get(t.table_type, 0)} for t in tables],
        'busy': [{'tableUid': b.table_uid,
                  'startTime': b.start_time.isoformat(),
                  'endTime': b.end_time.isoformat(),
                  # Their own bookings are labelled; everyone else's are anonymous.
                  'mine': b.customer_id == g.customer.id} for b in bookings],
    })


@customer_bp.route('/bookings', methods=['GET'])
@require_customer
def my_bookings():
    """Only ever this customer's own bookings."""
    # Unlike the staff strip (which lists only what still needs starting), the
    # guest keeps seeing their booking once it's under way — it's their session.
    rows = (Booking.query
            .filter(Booking.customer_id == g.customer.id,
                    Booking.status.in_(['booked', 'active']))
            .order_by(Booking.start_time)
            .all())
    return jsonify({'bookings': [{
        'id': b.id, 'code': b.code, 'tableUid': b.table_uid, 'tableType': b.table_type,
        'tableNumber': b.table_number,
        'guestName': b.guest_name,
        'startTime': b.start_time.isoformat(),
        'endTime': b.end_time.isoformat(),
        'status': b.status,
    } for b in rows]})


@customer_bp.route('/bookings', methods=['POST'])
@require_customer
@rate_limit(limit=20, window_seconds=3600)
def create_booking():
    data = request.json or {}
    try:
        start = datetime.fromisoformat(data['startTime'])
        end = datetime.fromisoformat(data['endTime'])
    except (KeyError, ValueError):
        return jsonify({'error': 'Valid start and end times are required'}), 400

    if end <= start:
        return jsonify({'error': 'End time must be after the start time'}), 400
    if (end - start).total_seconds() / 60 < MIN_BOOKING_MINUTES:
        return jsonify({'error': f'Minimum booking is {MIN_BOOKING_MINUTES} minutes'}), 400
    if start < datetime.now() - timedelta(minutes=1):
        return jsonify({'error': 'That start time has already passed'}), 400

    table = PoolTable.query.filter_by(uid=data.get('tableUid')).first()
    if not table:
        return jsonify({'error': 'That station no longer exists'}), 404

    # Whole-interval overlap, same rule the staff endpoint enforces. Checked
    # here too because the client's version of this is only a convenience.
    clash = next((b for b in Booking.query.filter(
        Booking.table_uid == table.uid,
        Booking.status.in_(['booked', 'active'])).all()
        if b.start_time < end and start < b.end_time), None)
    if clash:
        return jsonify({'error': 'That station is already booked for this time'}), 409

    booking = Booking(
        branch_id=table.branch_id,   # a booking always belongs to its table's branch
        table_uid=table.uid,
        table_type=table.table_type,
        table_number=table.table_id,
        guest_name=g.customer.name,
        phone=g.customer.phone,
        customer_id=g.customer.id,
        start_time=start,
        end_time=end,
        code=generate_booking_code(),
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({'success': True, 'id': booking.id, 'code': booking.code}), 201


@customer_bp.route('/bookings/<int:booking_id>', methods=['DELETE'])
@require_customer
def cancel_booking(booking_id):
    booking = Booking.query.filter_by(id=booking_id, customer_id=g.customer.id).first()
    # Filtering by customer_id in the QUERY, not after fetching, so another
    # guest's booking id simply doesn't exist from here.
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    if booking.status == 'active':
        return jsonify({'error': "This session has already started — speak to the front desk"}), 409
    booking.status = 'cancelled'
    booking.deleted_at = datetime.now()
    booking.deleted_by = f'customer:{g.customer.name}'
    db.session.commit()
    return jsonify({'success': True})

# ── game history ────────────────────────────────────────────────────────────

@customer_bp.route('/games', methods=['GET'])
@require_customer
def games():
    """This customer's completed sessions, plus lifetime totals.

    A session appears here when this account was ON it — as the tab owner
    (PlaySession.customer_id) or as any linked player on the roster
    (SessionPlayer.customer_id). Owner-only attribution missed anyone who
    joined a shared tab as the second, third or fourth member. Walk-in names
    carry no customer_id and never match, so a guest still sees only their own
    play, never anyone else's.

    `summary` is computed over EVERY session, while `games` is only the most
    recent page. Deriving the totals from the page would silently under-report
    as soon as someone has played more than `limit` times.
    """
    try:
        limit = min(max(int(request.args.get('limit', 20)), 1), 100)
    except (TypeError, ValueError):
        limit = 20

    # Owner OR roster member — deduplicated, because the owner is also on the
    # roster and would otherwise be counted twice.
    owned = PlaySession.query.filter_by(customer_id=g.customer.id).all()
    played = SessionPlayer.query.filter_by(customer_id=g.customer.id).all()
    session_ids = list({s.id for s in owned} | {sp.session_id for sp in played})
    if not session_ids:
        return jsonify({'games': [], 'summary': {
            'gamesPlayed': 0, 'minutesPlayed': 0, 'favourite': None}})

    logs = (ActivityLog.query
            .filter(ActivityLog.session_id.in_(session_ids))
            .order_by(ActivityLog.id.desc())
            .all())

    plays_by_type = {}
    total_minutes = 0
    for log in logs:
        total_minutes += log.billable_mins or 0
        plays_by_type[log.table_type] = plays_by_type.get(log.table_type, 0) + 1

    favourite = None
    if plays_by_type:
        table_type, plays = max(plays_by_type.items(), key=lambda kv: kv[1])
        favourite = {'type': table_type, 'plays': plays}

    return jsonify({
        'games': [{
            'id': log.id,
            'receiptId': log.receipt_id,
            'tableType': log.table_type,
            'tableNumber': log.table_id,
            'lounge': log.lounge,
            'elapsed': log.elapsed,
            'minutes': log.billable_mins,
            'cost': log.total_cost,
            'date': log.date_string,
            # Older rows predate this column; the client falls back to `date`.
            'playedAt': log.created_at.isoformat() if log.created_at else None,
        } for log in logs[:limit]],
        'summary': {
            'gamesPlayed': len(logs),
            'minutesPlayed': total_minutes,
            'favourite': favourite,
        },
    })


@customer_bp.route('/games/<int:log_id>/receipt', methods=['GET'])
@require_customer
def game_receipt(log_id):
    """The full itemised bill for one of this customer's own sessions.

    Ownership is enforced by resolving the log's session and checking it belongs
    to the caller — a log id from someone else's session simply 404s, so this
    can't be walked to read other people's bills.
    """
    log = ActivityLog.query.get(log_id)
    if not log or not log.session_id:
        return jsonify({'error': 'Receipt not found'}), 404

    session = PlaySession.query.get(log.session_id)
    if not session or session.customer_id != g.customer.id:
        return jsonify({'error': 'Receipt not found'}), 404

    try:
        segments = json.loads(log.segments_json) if log.segments_json else []
    except (ValueError, TypeError):
        segments = []

    # Shaped exactly like the invoice the staff receipt component renders, so
    # the same presentation can be reused without a translation layer.
    return jsonify({'receipt': {
        'receiptId': log.receipt_id,
        'date': log.date_string,
        'lounge': log.lounge,
        'tableType': log.table_type,
        'tableId': log.table_id,
        'player': log.player,
        'elapsed': log.elapsed,
        'billableMins': log.billable_mins,
        'rate': log.rate,
        'paymentStatus': log.payment_status,
        'paymentMethod': log.payment_method,
        'totalCost': log.total_cost,
        'segments': segments,
    }})

# ── khata ───────────────────────────────────────────────────────────────────

@customer_bp.route('/khata', methods=['GET'])
@require_customer
def my_khata():
    """What this guest currently owes.

    Two ways a bill reaches here: a session billed to their account, or a
    canteen sale put on a khata under their name. Matching on name is
    deliberately case-insensitive and exact — a loose match could show one guest
    another guest's debt.
    """
    bills = []

    sessions = (ActivityLog.query
                .filter(ActivityLog.payment_status == 'pending',
                        ActivityLog.customer_id == g.customer.id)
                .order_by(ActivityLog.id.desc())
                .all())
    for row in sessions:
        bills.append({
            'kind': 'session', 'id': row.id, 'ref': row.receipt_id, 'date': row.date_string,
            'label': f'{(row.table_type or "").title()} #{row.table_id}',
            'total': row.total_cost,
            # Per bill, so a guest can clear one and leave the rest.
            'payUrl': (_pay_link(amount=row.total_cost, kind='session',
                                 reference=str(row.receipt_id),
                                 payer_name=g.customer.name or '', log_id=row.id)
                       if _pay_link else None),
        })

    name = (g.customer.name or '').strip().lower()
    if name:
        orders = (CanteenOrder.query
                  .filter(CanteenOrder.status == 'paid',
                          CanteenOrder.payment_status == 'pending',
                          # A tab order counts once its session has ended.
                          db.or_(CanteenOrder.payment_method != 'tab',
                                 CanteenOrder.bill_group.isnot(None)),
                          db.func.lower(CanteenOrder.khata_name) == name)
                  .order_by(CanteenOrder.id.desc())
                  .all())
        for order in orders:
            bills.append({
                'kind': 'canteen', 'id': order.id, 'ref': order.order_no,
                'date': order.created_at.isoformat() if order.created_at else '',
                'label': 'Canteen', 'total': order.total,
                'payUrl': (_pay_link(amount=order.total, kind='canteen',
                                     reference=order.order_no,
                                     payer_name=g.customer.name or '', order_id=order.id)
                           if _pay_link else None),
            })

    outstanding = sum(b['total'] for b in bills)

    return jsonify({
        'outstanding': outstanding,
        # One code that clears everything owed. Paying it marks every bill below
        # as settled in a single go.
        'payUrl': (_pay_link(amount=outstanding, kind='account',
                             reference=f'ACCT-{g.customer.id}',
                             payer_name=g.customer.name or '',
                             customer_id=g.customer.id)
                   if _pay_link and outstanding else None),
        'bills': bills,
        # Settling is a staff action: money changes hands at the counter and
        # only the till can confirm it was received. The app shows the balance
        # and a payment code; it must not let a guest mark their own debt paid.
        'settleAtCounter': True,
    })