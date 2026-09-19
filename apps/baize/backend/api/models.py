from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime
from security import hash_password, verify_password
import os
import secrets
import string

# from flask_security import UserMixin, RoleMixin


db = SQLAlchemy()

# ── Multi-branch ──────────────────────────────────────────────────────────
# A Branch is a physical location of the (single, licensed) club. Every
# operational row carries a nullable branch_id; a staff member is attached to
# one or more branches via user_branches, with primary_branch_id as home.
user_branches = db.Table(
    'user_branches',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('branch_id', db.Integer, db.ForeignKey('branch.id', ondelete='CASCADE'), primary_key=True),
)


class SyncMixin:
    """Shared sync tracking for entities that replicate between a local install
    and the cloud (Phase 2). `sync_id` is the STABLE cross-boundary identity
    (never the integer PK); `updated_at` is the change watermark the sync engine
    pages on. `deleted_at` (soft delete) lives on the entities that support it."""
    sync_id = db.Column(db.String(36), index=True, default=lambda: str(uuid.uuid4()))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())


class SyncCursor(db.Model):
    """Per-entity high-water marks for this install's sync worker (local side).
    One row per entity type: how far we've pushed to / pulled from the cloud."""
    __tablename__ = 'sync_cursor'
    entity = db.Column(db.String(40), primary_key=True)
    last_pushed_at = db.Column(db.DateTime, nullable=True)
    last_pulled_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())


class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50), unique=True, nullable=False)   # stable client-facing id
    name = db.Column(db.String(100), nullable=False, default='Main Branch')
    address = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.String(80), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'uid': self.uid, 'name': self.name, 'address': self.address,
                'status': self.status, 'isDefault': self.is_default, 'sortOrder': self.sort_order}


class Queue(SyncMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Auto-incrementing primary key
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)    # soft delete: when it was removed
    deleted_by = db.Column(db.String(80), nullable=True)  # soft delete: who removed it
    # Optional: a name is a nicety, the callable number is the identity.
    guest_name = db.Column(db.String(100), nullable=True, default='')
    table_type = db.Column(db.String(50))  # e.g., 'pool', 'snooker', 'vip-snooker'
    # The number the counter calls out. Assigned server-side as the next after
    # the highest still waiting, so it climbs while the queue has people and
    # starts over at 1 once it empties.
    number = db.Column(db.Integer, nullable=True)
    uid = db.Column(db.BigInteger, unique=True, nullable=False)  # client-supplied id (may be a timestamp) — BigInteger avoids overflow
    # Scope of the request. Both null = any free table of this type, anywhere.
    # lounge only = any free table of this type in that lounge. Both set =
    # that specific table. (No FKs: a lounge/table can be removed while a
    # guest waits; the matcher treats a dangling ref as 'no longer available'.)
    lounge_uid = db.Column(db.String(50), nullable=True)
    table_uid = db.Column(db.String(50), nullable=True)

class Lounge(SyncMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)    # soft delete: when it was removed
    deleted_by = db.Column(db.String(80), nullable=True)  # soft delete: who removed it
    uid = db.Column(db.String(50), unique = True, nullable=False)
    name = db.Column(db.String(100), nullable=False, default='Lounge')
    status = db.Column(db.String(20), nullable=False, default='active')
    sort_order = db.Column(db.Integer, default=0)

class PoolTable(SyncMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)    # soft delete: when it was removed
    deleted_by = db.Column(db.String(80), nullable=True)  # soft delete: who removed it
    uid = db.Column(db.String(50), unique=True, nullable=False)
    table_id = db.Column(db.String(20), nullable=False)
    table_type = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    booking_name = db.Column(db.String(100), default='')
    start_time = db.Column(db.DateTime, nullable=True)  # UTC timestamp when the CURRENT segment started
    sort_order = db.Column(db.Integer, default=0)
    lounge_uid = db.Column(db.String, db.ForeignKey('lounge.uid'), nullable=True)
    # Tab currently attached to this station. Stays attached after a stop so the
    # session can be resumed; cleared when the tab is closed or a new one starts.
    session_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String, nullable=False, default='active')


class PlaySession(SyncMixin, db.Model):
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True, index=True)
    """One guest's tab. Survives transfers between stations and stop/resume cycles."""
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(100), default='')
    status = db.Column(db.String(20), default='active')  # active | stopped | settled
    receipt_id = db.Column(db.Integer, nullable=False)   # stable across resumes
    # Set when the tab was started from a customer's booking. This is the ONLY
    # link between a played session and an account — walk-ins stay anonymous.
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())


class SessionPlayer(SyncMixin, db.Model):
    """One person on a tab.

    A session can carry several — four friends on one table is the normal case,
    not the exception. `customer_id` is set only when staff linked a real
    account by phone; a name typed at the counter stays a name, because most
    walk-ins have no account and pretending otherwise would attach play history
    to the wrong person.
    """
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('play_session.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, default='')
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True, index=True)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now())


class SessionSegment(SyncMixin, db.Model):
    """A continuous stretch of play on one station at one rate.

    A new segment opens on every transfer and on every resume, so a tab that
    moved from pool to snooker bills each stretch at that station's own rate.
    """
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('play_session.id'), nullable=False)
    table_uid = db.Column(db.String(50), nullable=False)
    table_type = db.Column(db.String(30), nullable=False)
    table_number = db.Column(db.Integer)
    lounge_name = db.Column(db.String(100), default='')
    rate = db.Column(db.Integer, nullable=False)         # captured when the segment opens
    start_time = db.Column(db.DateTime, nullable=False)  # naive UTC
    end_time = db.Column(db.DateTime, nullable=True)     # None = still running


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMER IDENTITY — deliberately NOT part of `User`.
#
# `User` is staff: created by the owner, small, trusted, role-bearing.
# `Customer` is the public: self-registered, unbounded, untrusted.
#
# Keeping them in separate tables means no bug in customer signup can ever
# produce a row that the staff guard would accept — there is no `role` column
# to set, and no shared primary key space. This is structural, not a check that
# somebody has to remember to write.
# ─────────────────────────────────────────────────────────────────────────────

class Customer(SyncMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Canonical '+92XXXXXXXXXX'. Unique because this IS the account.
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    # Required: one-time codes are delivered here. An account without an email
    # can never be recovered.
    email = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        ok, upgraded = verify_password(self.password_hash, password)
        if ok and upgraded:                 # migrate a legacy/outdated hash in place
            self.password_hash = upgraded
            db.session.commit()
        return ok


class PasswordResetCode(db.Model):
    """A one-time code emailed to a customer.

    The code itself is hashed — a leaked database read shouldn't hand over live
    reset codes. Attempts are counted so the six-digit space can't be walked.
    """
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False, index=True)
    code_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())


class GlobalRate(SyncMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True, index=True)
    table_type = db.Column(db.String(50), nullable=False)
    weekday_rate = db.Column(db.Integer, nullable=False, default=0)
    weekend_rate = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.UniqueConstraint('branch_id', 'table_type', name='uq_branch_table_type'),
    )

class TableType(db.Model):
    """The single source of truth for station types (label, colour, which card
    renders it). Everything else references these by `key`."""
    __tablename__ = 'table_type'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(40), unique=True, nullable=False)          # e.g. 'ps5'
    label = db.Column(db.String(60), nullable=False)
    color = db.Column(db.String(9), nullable=False, default='#818cf8')   # hex, drives all styling
    renderer = db.Column(db.String(20), nullable=False, default='pool')  # pool|playstation|xbox|foosball
    badge = db.Column(db.String(6), nullable=False, default='?')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # A standard, inactive table object for previewing this type's card in the UI
    # (see PoolTable.vue). Only the fields a display card reads.
    sample_object = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        # id/value/key all alias the key so every existing consumer keeps working.
        return {'key': self.key, 'id': self.key, 'value': self.key,
                'label': self.label, 'color': self.color,
                'renderer': self.renderer, 'badge': self.badge, 'sortOrder': self.sort_order,
                'sampleObject': self.sample_object}

class Booking(SyncMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)    # soft delete: when it was removed
    deleted_by = db.Column(db.String(80), nullable=True)  # soft delete: who removed it
    # A short handle the counter matches against the guest's, since names
    # collide and can't be verified. Six uppercase letters (see
    # generate_booking_code). Indexed for counter lookup.
    code = db.Column(db.String(6), nullable=True, index=True)
    table_uid = db.Column(db.String(50), nullable=False)   # which station
    table_type = db.Column(db.String(30), nullable=False)  # denormalized for display
    table_number = db.Column(db.Integer)                   # denormalized for display
    guest_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    # Set when a guest booked it themselves through the portal; NULL for
    # bookings taken at the counter by staff.
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True, index=True)
    start_time = db.Column(db.DateTime, nullable=False)     # when they want it
    end_time = db.Column(db.DateTime, nullable=False)     # when they want it
    # booked   -> reserved, not yet started
    # active   -> staff started the session; still running, not yet billed
    # completed-> the session was ended and billed
    # cancelled-> called off before it started
    status = db.Column(db.String(20), default='booked')
    # Set when the booking is started, so ending that session can complete it.
    session_id = db.Column(db.Integer, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())


def generate_booking_code():
    """A short handle the counter can match against the guest's.

    Six uppercase letters (26**6 ≈ 300M) drawn with `secrets`, so a code can't
    be guessed to claim someone else's slot. Uniqueness is enforced only against
    bookings that still matter (booked/active) — once one is completed or
    cancelled its code is free to reappear. Called inside a request, so the
    Booking query runs within an app context.
    """
    for _ in range(20):
        code = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(6))
        clash = Booking.query.filter(
            Booking.code == code,
            Booking.status.in_(['booked', 'active'])).first()
        if not clash:
            return code
    return code  # 20 straight collisions is astronomically unlikely


class ActivityLog(SyncMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True, index=True)
    receipt_id = db.Column(db.Integer, nullable=False)
    date_string = db.Column(db.String(50), nullable=False)
    lounge = db.Column(db.String(100), default='')
    table_type = db.Column(db.String(30), nullable=False)
    table_id = db.Column(db.String(20), nullable=False)
    player = db.Column(db.String(100), nullable=False)
    elapsed = db.Column(db.String(20), nullable=False)
    billable_mins = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Integer, nullable=False)
    # One ledger row per tab: resuming and stopping again UPDATES this row
    # rather than adding a second one, so revenue is never double counted.
    session_id = db.Column(db.Integer, nullable=True)
    segments_json = db.Column(db.Text, nullable=True)  # per-station breakdown
    # Canteen items charged to this tab, and the play/canteen split. Stored on
    # the row so a reopened bill shows exactly what the guest was handed —
    # rebuilding it later would use today's prices, not that night's.
    canteen_json = db.Column(db.Text, nullable=True)
    play_total = db.Column(db.Integer, nullable=True)
    canteen_total = db.Column(db.Integer, nullable=True)
    split_count = db.Column(db.Integer, nullable=True)
    # date_string is for display; this is the sortable/relative-time value.
    created_at = db.Column(db.DateTime, nullable=True)
    served_by = db.Column(db.String(80), default='')             # staff username
    # pending -> owed (this is what "khata" means: an unpaid running account)
    # paid    -> settled
    payment_status = db.Column(db.String(20), default='pending', nullable=False)
    # How it was settled: cash | easypaisa | jazzcash | account. Empty while
    # unpaid. Every ledger row records this, so takings can be reconciled
    # against the drawer without guessing.
    payment_method = db.Column(db.String(20), default='')
    settled_at = db.Column(db.DateTime, nullable=True)
    # Who owes it. Only set for credit — a walk-in has nobody to chase.
    khata_name = db.Column(db.String(100), nullable=True)
    customer_id = db.Column(db.Integer, nullable=True, index=True)
    # When the counter finished with this bill. A bill is closed only after it
    # has been settled — paid, or placed on someone's account — so closing is a
    # record that the money was dealt with, not a way to make it disappear.
    closed_at = db.Column(db.DateTime, nullable=True, index=True)
    closed_by = db.Column(db.String(80), nullable=True)
    # Ties a table bill to the canteen orders that rode its tab. The guest is
    # handed one combined total; the books keep separate rows so canteen
    # revenue is never counted as table revenue. One payment clears the group.
    bill_group = db.Column(db.String(40), nullable=True, index=True)

# ─────────────────────────────────────────────────────────────────────────────
# CANTEEN
# ─────────────────────────────────────────────────────────────────────────────

class CanteenProduct(SyncMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)    # soft delete: when it was removed
    deleted_by = db.Column(db.String(80), nullable=True)  # soft delete: who removed it
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(30), nullable=False, index=True)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=True)
    emoji = db.Column(db.String(16), default='')
    img_url = db.Column(db.String(255), nullable=True) # Added field[cite: 3]
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)


class CanteenOrder(SyncMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True, index=True)
    order_no = db.Column(db.String(20), unique=True, nullable=False)
    target_label = db.Column(db.String(60), default='Walk-in')   # for display
    table_uid = db.Column(db.String(50), nullable=True)          # when charged to a station
    session_id = db.Column(db.Integer, nullable=True)            # the tab it rides on
    subtotal = db.Column(db.Integer, nullable=False)
    discount_percent = db.Column(db.Integer, default=0, nullable=False)
    discount_amount = db.Column(db.Integer, default=0, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(20), default='cash')
    # Counter sales are settled at the till; a bill left on khata stays pending.
    payment_status = db.Column(db.String(20), default='pending', nullable=False)
    settled_at = db.Column(db.DateTime, nullable=True)
    khata_name = db.Column(db.String(100), nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True, index=True)
    closed_by = db.Column(db.String(80), nullable=True)
    # Set when this order rode a table's tab; see ActivityLog.bill_group.
    bill_group = db.Column(db.String(40), nullable=True, index=True)
    status = db.Column(db.String(20), default='paid')            # paid | void
    served_by = db.Column(db.String(80), default='')             # staff username
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Boolean, nullable=False) 

class CanteenOrderItem(SyncMixin, db.Model):
    """Line items snapshot the name and price AT SALE TIME.

    A later price change or product rename must not silently rewrite history —
    yesterday's receipt has to keep showing what was actually charged.
    """
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('canteen_order.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    line_total = db.Column(db.Integer, nullable=False)


class PaymentIntent(db.Model):
    """A request for money that a guest can scan and pay.

    DEMO: confirming an intent simply marks it paid — there is no gateway
    behind it yet. The shape is what a real EasyPaisa/JazzCash callback would
    populate, so wiring one in later means filling `confirm` differently rather
    than rebuilding this.
    """
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(40), unique=True, nullable=False, index=True)
    # What is being paid for: 'session' | 'canteen' | 'account'
    kind = db.Column(db.String(20), nullable=False, default='session')
    reference = db.Column(db.String(40), default='')      # receipt no / order code
    amount = db.Column(db.Integer, nullable=False, default=0)
    payer_name = db.Column(db.String(100), default='')     # who the bill is for
    paid_by = db.Column(db.String(100), default='')        # who actually paid
    method = db.Column(db.String(20), default='')          # easypaisa | jazzcash
    status = db.Column(db.String(20), default='pending')   # pending | paid | cancelled
    # Where the money should land once paid, so confirming can settle the bill.
    log_id = db.Column(db.Integer, nullable=True)
    canteen_order_id = db.Column(db.Integer, nullable=True)
    customer_id = db.Column(db.Integer, nullable=True)
    # Staff are notified once; this stops the same payment pinging forever.
    seen_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    paid_at = db.Column(db.DateTime, nullable=True)


class License(db.Model):
    """The club's activated license — an Ed25519-signed token plus its parsed
    claims. The token is the source of truth (re-verified on every check); the
    columns are a convenience mirror for display and queries. One row per club;
    a renewal updates it in place and keeps the uploaded logo.
    """
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text, nullable=False)                 # the signed JWT
    club_uid = db.Column(db.String(80), unique=True, nullable=False, index=True)
    club_name = db.Column(db.String(120), nullable=False)      # branded display name
    issued_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    activated_at = db.Column(db.DateTime, default=lambda: datetime.now())
    last_seen_at = db.Column(db.DateTime, nullable=True)        # clock-rollback guard baseline
    system_identifier = db.Column(db.String(), nullable=True)  # JSON list of enrolled device fingerprints
    logo_url = db.Column(db.String(255), nullable=True)        # club-uploaded logo
    entitlements = db.Column(db.Text, default='[]')   # JSON list of licensed module keys
    # Server heartbeat state (set by license_util when LICENSE_SERVER_URL is configured).
    server_status = db.Column(db.String(20), default="unknown")   # last heartbeat verdict
    server_checked_at = db.Column(db.DateTime, nullable=True)      # last successful beat
    revoked_at = db.Column(db.DateTime, nullable=True)             # sticky: server said revoked/suspended


class BranchLicense(db.Model):
    """A per-branch license activated on this install — the child token issued by
    the license server (carries a `branch` claim + that branch's own `ent`).
    Features and revocation are per-branch; the token is the source of truth,
    these columns are a display/heartbeat mirror. Linked to a local Branch by uid."""
    id = db.Column(db.Integer, primary_key=True)
    branch_uid = db.Column(db.String(50), unique=True, nullable=False, index=True)  # == token `branch` == Branch.uid
    club_uid = db.Column(db.String(80), nullable=False, index=True)                 # token `sub` (parent club)
    name = db.Column(db.String(100), default='Branch')
    token = db.Column(db.Text, nullable=False)
    entitlements = db.Column(db.Text, default='[]')          # display mirror; gating uses the verified token
    issued_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    system_identifier = db.Column(db.Text, nullable=True)
    server_status = db.Column(db.String(20), default='unknown')
    server_checked_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)       # sticky: server said revoked
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deleted_at = db.Column(db.DateTime, nullable=True)    # soft delete: when it was removed
    deleted_by = db.Column(db.String(80), nullable=True)  # soft delete: who removed it
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='receptionist')  # owner | manager | receptionist
    # Which counters this person may work, comma-separated: 'floor', 'canteen'.
    # Only meaningful for a receptionist — managers and owners cover everything,
    # so storing it for them would be a second source of truth that could drift.
    capabilities = db.Column(db.String(120), nullable=False, default='floor')
    primary_branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)
    branches = db.relationship('Branch', secondary=user_branches, lazy='joined',
                               backref=db.backref('users', lazy='selectin'))
 
    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        ok, upgraded = verify_password(self.password_hash, password)
        if ok and upgraded:                 # migrate a legacy/outdated hash in place
            self.password_hash = upgraded
            db.session.commit()
        return ok