"""
Baize licensing server (VENDOR side — its own repo, its own Postgres).

Clubs self-register (their own account), the vendor administers them and mints
Ed25519-signed license tokens, and the Baize app fetches a club's token to
activate an install. The vendor's private key lives here — keep this host locked.

    Club 1──* Device      (fingerprints the club enrolled)
    Club 1──* License     (signed tokens issued to that club)
    AdminEvent            (audit trail of every vendor action)
"""
import datetime as dt
import functools
import glob
import json
import os
import secrets
import uuid

import jwt
from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from dotenv import load_dotenv
from flask_migrate import Migrate
import argparse
import httpx

import signing

load_dotenv()
_ph = PasswordHasher()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DIST_DIR = os.path.join(BASE_DIR, "../dist")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)

CORS(app, resources={r"/*": {"origins": os.environ.get("CORS_ORIGINS", "*").split(",")}})

CLUB_JWT_SECRET = os.environ.get("CLUB_JWT_SECRET", "change-me-club-secret")
CENTRAL_URL = os.environ.get("CENTRAL_URL", "")            # baize-customer base URL
REGISTRY_ADMIN_KEY = os.environ.get("REGISTRY_ADMIN_KEY", "")  # shared with the central app
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")                       # vendor master token
ADMIN_JWT_SECRET = os.environ.get("ADMIN_JWT_SECRET", CLUB_JWT_SECRET)  # signs short-lived admin sessions
ADMIN_SESSION_HOURS = int(os.environ.get("ADMIN_SESSION_HOURS", "12"))
AUTO_TRIAL_DAYS = int(os.environ.get("AUTO_TRIAL_DAYS", "0"))
MODULES = {"playstation", "xbox", "pc", "foosball", "tabletennis", "canteen", "insights", "bookings", "payments"}   # gated add-ons
EXPIRING_SOON_DAYS = int(os.environ.get("EXPIRING_SOON_DAYS", "7"))


# ── time helpers: store naive-UTC, serialize as explicit UTC ────────────────

def _utcnow():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def _naive(v):
    return v.replace(tzinfo=None) if (v and v.tzinfo is not None) else v


def _iso(v):
    if not v:
        return None
    if v.tzinfo is None:
        v = v.replace(tzinfo=dt.timezone.utc)
    return v.isoformat()


def _days_left(expires_at):
    if not expires_at:
        return None
    return (_naive(expires_at) - _utcnow()).days


# ── models ───────────────────────────────────────────────────────────────────

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(40), unique=True, nullable=False, index=True)  # token `sub` / tenant key
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    club_name = db.Column(db.String(120), nullable=False)
    owner_name = db.Column(db.String(120), default="")
    phone = db.Column(db.String(40), default="")
    address = db.Column(db.String(255), default="")
    city = db.Column(db.String(80), default="")
    country = db.Column(db.String(80), default="")
    plan = db.Column(db.String(40), default="local")        # local | online | trial
    notes = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    registered = db.Column(db.Boolean, default=False)
    devices = db.relationship("Device", backref="club", cascade="all, delete-orphan")
    licenses = db.relationship("License", backref="club", cascade="all, delete-orphan")
    branches = db.relationship("Branch", backref="club", cascade="all, delete-orphan")

    def public(self):
        return {"uuid": self.uuid, "email": self.email, "clubName": self.club_name,
                "ownerName": self.owner_name, "phone": self.phone, "address": self.address,
                "city": self.city, "country": self.country, "plan": self.plan,
                "notes": self.notes or "", "isActive": self.is_active,
                "deviceCount": len(self.devices), "licenseCount": len(self.licenses),
                "branchCount": len([b for b in self.branches if b._status != "archived"]),
            "licenseStatus": (max(self.licenses, key=lambda x: x.id).status if self.licenses else "none"),
                "createdAt": _iso(self.created_at)}


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("club.id"), nullable=False, index=True)
    fingerprint = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(80), default="")
    created_at = db.Column(db.DateTime, default=_utcnow)
    __table_args__ = (db.UniqueConstraint("club_id", "fingerprint", name="uq_club_device"),)

    def public(self):
        return {"id": self.id, "fingerprint": self.fingerprint, "label": self.label or "",
                "createdAt": _iso(self.created_at)}


class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("club.id"), nullable=False, index=True)
    token = db.Column(db.Text, nullable=False)
    activation_code = db.Column(db.String(16), nullable=False, index=True)
    devices = db.Column(db.Text, default="[]")               # JSON list bound into the token
    issued_at = db.Column(db.DateTime, default=_utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    _status = db.Column("status", db.String(20), default="active")   # active | revoked (expired is derived)

    # Derived status (Python-side, evaluated at call time). We never compare
    # status in SQL — queries use _status + expires_at explicitly — so there's
    # no stale import-time `now` bug.
    @property
    def status(self):
        if self._status == "revoked":
            return "revoked"
        if self.expires_at is not None and _utcnow() > _naive(self.expires_at):
            return "expired"
        return self._status or "active"

    @property
    def device_list(self):
        try:
            return json.loads(self.devices or "[]")
        except ValueError:
            return []

    def public(self, with_token=False, with_club=False):
        devs = self.device_list
        d = {"id": self.id, "activationCode": self.activation_code, "status": self.status,
             "deviceBound": bool(devs), "deviceCount": len(devs),
             "issuedAt": _iso(self.issued_at), "expiresAt": _iso(self.expires_at),
             "daysLeft": _days_left(self.expires_at)}
        try:
            d["modules"] = signing.inspect(self.token).get("ent", [])
            d["branches"] = signing.inspect(self.token).get("branches", 1)
        except Exception:
            d["modules"] = []
        if with_token:
            d["token"] = self.token
        if with_club and self.club:
            d["clubUuid"] = self.club.uuid
            d["clubName"] = self.club.club_name
        return d


class Branch(db.Model):
    """A child of a Club, individually licensed with its OWN feature set. Each
    branch has its own signed token (with a `branch` claim) so features and
    revocation are per-branch, independent of siblings."""
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("club.id"), nullable=False, index=True)
    uid = db.Column(db.String(40), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, default="Branch")
    address = db.Column(db.String(255), default="")         # branch location
    features = db.Column(db.Text, default="[]")             # JSON list of this branch's modules
    token = db.Column(db.Text, nullable=True)
    devices = db.Column(db.Text, default="[]")              # JSON fingerprints bound into the branch token
    activation_code = db.Column(db.String(16), nullable=True, index=True)
    issued_at = db.Column(db.DateTime, default=_utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    _status = db.Column("status", db.String(20), default="active")   # active | revoked | archived
    created_at = db.Column(db.DateTime, default=_utcnow)

    @property
    def status(self):
        if self._status in ("revoked", "archived"):
            return self._status
        if self.expires_at and _utcnow() > _naive(self.expires_at):
            return "expired"
        return "active"

    def feature_list(self):
        try:
            return json.loads(self.features or "[]")
        except ValueError:
            return []

    def public(self, with_token=False):
        d = {"id": self.id, "uid": self.uid, "name": self.name, "address": self.address or "",
             "features": self.feature_list(), "status": self.status,
             "activationCode": self.activation_code,
             "expiresAt": _iso(self.expires_at), "createdAt": _iso(self.created_at)}
        if with_token and self.token:
            d["token"] = self.token
        return d


class AdminEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(48), nullable=False)          # e.g. license.issue
    target_type = db.Column(db.String(40))                     # club | license | device
    target_id = db.Column(db.String(60))
    summary = db.Column(db.String(255), default="")
    meta = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    def public(self):
        try:
            meta = json.loads(self.meta or "{}")
        except ValueError:
            meta = {}
        return {"id": self.id, "action": self.action, "targetType": self.target_type,
                "targetId": self.target_id, "summary": self.summary or "",
                "meta": meta, "createdAt": _iso(self.created_at)}


def _log(action, target_type=None, target_id=None, summary="", **meta):
    db.session.add(AdminEvent(action=action, target_type=target_type,
                              target_id=str(target_id) if target_id is not None else None,
                              summary=summary, meta=json.dumps(meta or {}), created_at=_utcnow()))


# ── auth ─────────────────────────────────────────────────────────────────────

def _club_token(club):
    return jwt.encode({"sub": str(club.id), "exp": _utcnow() + dt.timedelta(days=30)},
                      CLUB_JWT_SECRET, algorithm="HS256")


def club_required(fn):
    @functools.wraps(fn)
    def wrap(*a, **kw):
        hdr = request.headers.get("Authorization", "")
        try:
            data = jwt.decode(hdr[7:] if hdr.startswith("Bearer ") else "",
                              CLUB_JWT_SECRET, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return jsonify({"error": "Please sign in."}), 401
        g.club = db.session.get(Club, int(data["sub"]))
        if not g.club or not g.club.is_active:
            return jsonify({"error": "Account not found or disabled."}), 401
        return fn(*a, **kw)
    return wrap


def _admin_ok():
    """Accept a short-lived admin JWT (Bearer) or the master token header."""
    hdr = request.headers.get("Authorization", "")
    if hdr.startswith("Bearer "):
        try:
            if jwt.decode(hdr[7:], ADMIN_JWT_SECRET, algorithms=["HS256"]).get("role") == "admin":
                return True
        except jwt.InvalidTokenError:
            pass
    return bool(ADMIN_TOKEN) and request.headers.get("X-Admin-Token") == ADMIN_TOKEN


def admin_required(fn):
    @functools.wraps(fn)
    def wrap(*a, **kw):
        if not _admin_ok():
            return jsonify({"error": "unauthorized"}), 401
        return fn(*a, **kw)
    return wrap


def _new_uuid():
    while True:
        uid = "club_" + uuid.uuid4().hex[:16]
        if not Club.query.filter_by(uuid=uid).first():
            return uid


def _paginate(rows):
    """Slice a Python list by ?page & ?perPage. Returns (items, meta)."""
    try:
        page = max(1, int(request.args.get("page", 1)))
        per = min(100, max(1, int(request.args.get("perPage", 25))))
    except ValueError:
        page, per = 1, 25
    total = len(rows)
    start = (page - 1) * per
    return rows[start:start + per], {"total": total, "page": page, "perPage": per,
                                     "pages": max(1, (total + per - 1) // per)}


def _main_license(club):
    return max(club.licenses, key=lambda x: x.id, default=None)


def _branch_cap(club):
    """How many branches this club may run — from its main licence's `branches`."""
    lic = _main_license(club)
    if not lic:
        return 1
    try:
        return max(1, int(signing.inspect(lic.token).get("branches", 1) or 1))
    except Exception:
        return 1


def _mint_branch(club, branch, devices, days):
    """Mint a branch's OWN signed token with its own explicit expiry, device
    binding and feature set. The branch is the licensing unit — there is no
    separate account licence for it to inherit (or drift) from."""
    days = max(1, int(days or 365))
    branch.expires_at = _utcnow() + dt.timedelta(days=days)
    branch.devices = json.dumps(list(devices or []))
    return signing.mint(club.uuid, club.club_name, days, list(devices or []),
                        modules=branch.feature_list(), branch=branch.uid)



def _do_register_branch(club, d):
    """Register a branch under a club and mint its per-branch token. There is no
    pre-set allowance — a club's branch count is simply however many branches
    have been registered here. Shared by the admin portal and the app."""
    import secrets as _sec
    features = [mod for mod in (d.get("features") or []) if mod in MODULES]
    name = (d.get("name") or "Branch").strip()[:120] or "Branch"
    address = (d.get("address") or "").strip()[:255]
    devices = d.get("devices") or []
    b = Branch(club_id=club.id, uid=f"br_{_sec.token_hex(6)}", name=name, address=address,
               features=json.dumps(features), devices=json.dumps(devices),
               activation_code=_sec.token_hex(4).upper(), _status="active")
    db.session.add(b)
    db.session.flush()
    b.token = _mint_branch(club, b, devices, 365)
    db.session.flush()
    _log("branch.register", "branch", b.id,
         summary=f"branch '{name}' for {club.club_name}", clubUuid=club.uuid, features=features)
    db.session.commit()
    return b, None

def _issue_license(club, days, devices, modules=None, branches=1):
    token = signing.mint(club.uuid, club.club_name, days, devices, modules, branches)
    lic = License(club_id=club.id, token=token, activation_code=secrets.token_hex(4).upper(),
                  devices=json.dumps(list(devices or [])),
                  expires_at=_utcnow() + dt.timedelta(days=int(days)))
    db.session.add(lic)
    return lic


# ── club account API (called by the Baize app) ──────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    d = request.json or {}
    email = (d.get("email") or "").strip().lower()
    password = d.get("password") or ""
    club_name = (d.get("clubName") or "").strip()
    if not (email and password and club_name):
        return jsonify({"error": "Club name, email and password are required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    if Club.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists."}), 409
    club = Club(uuid=_new_uuid(), email=email, password_hash=_ph.hash(password),
                club_name=club_name, owner_name=(d.get("ownerName") or "").strip(),
                phone=(d.get("phone") or "").strip(), address=(d.get("address") or "").strip(),
                city=(d.get("city") or "").strip(), country=(d.get("country") or "").strip(),
                plan=(d.get("plan") or "local"))
    db.session.add(club)
    db.session.flush()
    _log("club.register", "club", club.uuid, summary=f"{club.club_name} registered")
    if AUTO_TRIAL_DAYS > 0:
        _issue_license(club, AUTO_TRIAL_DAYS, [])
    db.session.commit()
    return jsonify({"token": _club_token(club), "club": club.public()}), 201


@app.route("/api/login", methods=["POST"])
def login():
    d = request.json or {}
    club = Club.query.filter_by(email=(d.get("email") or "").strip().lower()).first()
    try:
        assert club and club.is_active
        _ph.verify(club.password_hash, d.get("password") or "")
    except (AssertionError, Argon2Error):
        return jsonify({"error": "Invalid email or password."}), 401
    return jsonify({"token": _club_token(club), "club": club.public()})


@app.route("/api/me", methods=["GET"])
@club_required
def me():
    return jsonify({
        "club": g.club.public(),
        "devices": [dv.public() for dv in g.club.devices],
        "licenses": [lic.public(with_token=True) for lic in g.club.licenses],
    })


@app.route("/api/devices", methods=["POST"])
@club_required
def add_device():
    fp = (request.json or {}).get("fingerprint", "").strip()
    if not fp:
        return jsonify({"error": "Paste the device ID shown in the app."}), 400
    if not Device.query.filter_by(club_id=g.club.id, fingerprint=fp).first():
        db.session.add(Device(club_id=g.club.id, fingerprint=fp,
                              label=(request.json or {}).get("label", "").strip()))
        db.session.commit()
    return jsonify({"ok": True})


# ── admin: session ───────────────────────────────────────────────────────────

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    if not ADMIN_TOKEN:
        return jsonify({"error": "Admin access is not configured on this server."}), 503
    if (request.json or {}).get("token") != ADMIN_TOKEN:
        return jsonify({"error": "Invalid admin token."}), 401
    token = jwt.encode({"role": "admin", "exp": _utcnow() + dt.timedelta(hours=ADMIN_SESSION_HOURS)},
                       ADMIN_JWT_SECRET, algorithm="HS256")
    return jsonify({"token": token, "expiresInHours": ADMIN_SESSION_HOURS})


@app.route("/api/admin/whoami", methods=["GET"])
@admin_required
def admin_whoami():
    return jsonify({"ok": True})


# ── admin: stats ─────────────────────────────────────────────────────────────

@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def stats():
    now = _utcnow()
    counts = {"active": 0, "expired": 0, "revoked": 0}
    expiring = 0
    for lic in License.query.all():
        s = lic.status
        counts[s] = counts.get(s, 0) + 1
        if s == "active" and lic.expires_at is not None:
            if 0 <= (_naive(lic.expires_at) - now).days <= EXPIRING_SOON_DAYS:
                expiring += 1
    return jsonify({
        "clubs": Club.query.count(),
        "activeClubs": Club.query.filter_by(is_active=True).count(),
        "suspendedClubs": Club.query.filter_by(is_active=False).count(),
        "devices": Device.query.count(),
        "licenses": sum(counts.values()),
        "activeLicenses": counts["active"], "expiredLicenses": counts["expired"],
        "revokedLicenses": counts["revoked"], "expiringSoon": expiring,
        "expiringWindow": EXPIRING_SOON_DAYS,
    })


# ── admin: clubs ─────────────────────────────────────────────────────────────

@app.route("/api/admin/clubs", methods=["GET"])
@admin_required
def list_clubs():
    q = (request.args.get("q") or "").strip().lower()
    plan = request.args.get("plan")
    rows = Club.query.order_by(Club.created_at.desc()).all()
    if q:
        rows = [c for c in rows if q in (c.club_name or "").lower() or q in (c.email or "").lower()
                or q in (c.uuid or "").lower() or q in (c.city or "").lower()]
    if plan:
        rows = [c for c in rows if c.plan == plan]
    items, meta = _paginate(rows)
    return jsonify({"items": [c.public() for c in items], **meta})


@app.route("/api/admin/clubs/<club_uuid>", methods=["GET"])
@admin_required
def club_detail(club_uuid):
    club = Club.query.filter_by(uuid=club_uuid).first()
    if not club:
        return jsonify({"error": "No club with that UUID."}), 404
    return jsonify({
        "registered": club.registered,
        "club": club.public(),
        "devices": [dv.public() for dv in club.devices],
        "licenses": [lic.public(with_token=True) for lic in
                     sorted(club.licenses, key=lambda l: l.id, reverse=True)],
    })

@app.route("/api/admin/clubs/<club_uuid>/enlist", methods=["POST", "DELETE"])
@admin_required
def enlist_club(club_uuid):
    """Enlist (POST) or delist (DELETE) a club in the central customer registry."""
    club = Club.query.filter_by(uuid=club_uuid).first()
    if not club:
        return jsonify({"error": "No club with that UUID."}), 404
    if not CENTRAL_URL or not REGISTRY_ADMIN_KEY:
        return jsonify({"error": "Central registry not configured (CENTRAL_URL / REGISTRY_ADMIN_KEY)."}), 503

    base = CENTRAL_URL.rstrip("/")
    headers = {"X-Registry-Key": REGISTRY_ADMIN_KEY}
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            club_url = (data.get("clubUrl") or "").strip()
            if not club_url:
                return jsonify({"error": "A public URL is required to register the club."}), 400
            res = httpx.post(f"{base}/api/registry/clubs", headers=headers, timeout=10.0, json={
                "uuid": club.uuid, "clubName": club.club_name, "publicUrl": club_url,
                "city": club.city, "address": club.address, "country": club.country,
                "notes": club.notes or "",
            })
            if res.status_code >= 400:
                return jsonify({"error": f"Central registry rejected the request: {res.text}"}), 502
            club.registered = True
            _log("club.register", "club", club.uuid,
                 summary=f"{club.club_name} enlisted in central registry")
        else:  # DELETE
            res = httpx.delete(f"{base}/api/registry/clubs/{club.uuid}", headers=headers, timeout=10.0)
            if res.status_code >= 400 and res.status_code != 404:
                return jsonify({"error": f"Central registry rejected the request: {res.text}"}), 502
            club.registered = False
            _log("club.deregister", "club", club.uuid,
                 summary=f"{club.club_name} removed from central registry")
    except httpx.RequestError as e:
        return jsonify({"error": f"Could not reach the central registry: {e}"}), 502

    db.session.commit()
    return jsonify({"ok": True, "registered": club.registered})


@app.route("/api/admin/clubs/<club_uuid>", methods=["PATCH"])
@admin_required
def edit_club(club_uuid):
    club = Club.query.filter_by(uuid=club_uuid).first()
    if not club:
        return jsonify({"error": "No club with that UUID."}), 404
    d = request.json or {}
    for field, attr in [("clubName", "club_name"), ("ownerName", "owner_name"), ("phone", "phone"),
                        ("address", "address"), ("city", "city"), ("country", "country"),
                        ("plan", "plan"), ("notes", "notes")]:
        if field in d and d[field] is not None:
            setattr(club, attr, str(d[field]).strip() if attr != "notes" else str(d[field]))
    if "isActive" in d:
        club.is_active = bool(d["isActive"])
        _log("club.suspend" if not club.is_active else "club.reactivate", "club", club.uuid,
             summary=f"{club.club_name} {'suspended' if not club.is_active else 'reactivated'}")
    _log("club.edit", "club", club.uuid, summary=f"{club.club_name} details updated")
    db.session.commit()
    return jsonify(club.public())


# ── admin: devices ───────────────────────────────────────────────────────────

@app.route("/api/admin/devices", methods=["POST"])
@admin_required
def admin_add_device():
    d = request.json or {}
    club = Club.query.filter_by(uuid=d.get("clubUuid", "")).first()
    if not club:
        return jsonify({"error": "No club with that UUID."}), 404
    fp = (d.get("fingerprint") or "").strip()
    if not fp:
        return jsonify({"error": "Fingerprint is required."}), 400
    if not Device.query.filter_by(club_id=club.id, fingerprint=fp).first():
        db.session.add(Device(club_id=club.id, fingerprint=fp, label=(d.get("label") or "").strip()))
        _log("device.enroll", "device", fp, summary=f"Device enrolled for {club.club_name}",
             clubUuid=club.uuid)
        db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/devices/<int:device_id>", methods=["DELETE"])
@admin_required
def admin_remove_device(device_id):
    dev = db.session.get(Device, device_id)
    if not dev:
        return jsonify({"error": "Device not found."}), 404
    club_uuid = dev.club.uuid if dev.club else None
    db.session.delete(dev)
    _log("device.remove", "device", dev.fingerprint, summary="Device un-enrolled", clubUuid=club_uuid)
    db.session.commit()
    return jsonify({"ok": True})


# ── admin: licenses ──────────────────────────────────────────────────────────

@app.route("/api/admin/issue", methods=["POST"])
@admin_required
def issue():
    """Mint a token for a registered club. Binds the club's enrolled devices
    unless `devices` is given explicitly (empty list = unbound)."""
    d = request.json or {}
    club = Club.query.filter_by(uuid=d.get("clubUuid", "")).first()
    if not club:
        return jsonify({"error": "No club with that UUID."}), 404
    devices = d["devices"] if "devices" in d else [dv.fingerprint for dv in club.devices]
    days = int(d.get("days", 365))
    modules = [m for m in (d.get("modules") or []) if m in MODULES]
    branches = max(1, int(d.get("branches", 1) or 1))
    lic = _issue_license(club, days, devices, modules, branches)
    db.session.flush()
    _log("license.issue", "license", lic.id, summary=f"{days}-day license for {club.club_name}",
         clubUuid=club.uuid, days=days, bound=bool(devices), modules=modules, branches=branches)
    db.session.commit()
    return jsonify({"clubUuid": club.uuid, "license": lic.public(with_token=True, with_club=True)})


@app.route("/api/admin/clubs/<uuid>/branches", methods=["GET", "POST"])
@admin_required
def admin_branches(uuid):
    club = Club.query.filter_by(uuid=uuid).first_or_404()
    if request.method == "GET":
        return jsonify({"branches": [b.public(with_token=True) for b in club.branches
                                     if b._status != "archived"],
                        "count": len([b for b in club.branches if b._status != "archived"])})
    b, err = _do_register_branch(club, request.get_json(silent=True) or {})
    if err:
        return err
    return jsonify({"branch": b.public(with_token=True)}), 201


@app.route("/api/admin/branches/<int:bid>", methods=["PATCH"])
@admin_required
def admin_update_branch(bid):
    b = db.session.get(Branch, bid)
    if not b:
        return jsonify({"error": "No such branch."}), 404
    d = request.get_json(silent=True) or {}
    if "name" in d and (d["name"] or "").strip():
        b.name = d["name"].strip()[:120]
    if "features" in d:
        b.features = json.dumps([m for m in (d["features"] or []) if m in MODULES])
        remaining = max(1, (_naive(b.expires_at) - _utcnow()).days) if b.expires_at else 365
        b.token = _mint_branch(b.club, b, json.loads(b.devices or "[]"), remaining)   # keep expiry, new features
    _log("branch.update", "branch", b.id, summary=f"updated '{b.name}'", features=b.feature_list())
    db.session.commit()
    return jsonify({"branch": b.public(with_token=True)})


@app.route("/api/admin/branches/<int:bid>/mint", methods=["POST"])
@admin_required
def admin_mint_branch(bid):
    """Mint (or re-mint) a branch's own licence: sets its expiry + binding, and
    bundles its current feature set into a fresh signed token."""
    b = db.session.get(Branch, bid)
    if not b:
        return jsonify({"error": "No such branch."}), 404
    d = request.get_json(silent=True) or {}
    days = max(1, int(d.get("days", 365) or 365))
    devices = d["devices"] if "devices" in d else [dv.fingerprint for dv in b.club.devices]
    b.token = _mint_branch(b.club, b, devices, days)
    b._status = "active"
    _log("branch.mint", "branch", b.id, summary=f"{b.name} · {days}d", clubUuid=b.club.uuid)
    db.session.commit()
    return jsonify({"branch": b.public(with_token=True)})


@app.route("/api/admin/branches/<int:bid>/revoke", methods=["POST"])
@admin_required
def admin_revoke_branch(bid):
    b = db.session.get(Branch, bid)
    if not b:
        return jsonify({"error": "No such branch."}), 404
    b._status = "active" if b._status == "revoked" and (request.get_json(silent=True) or {}).get("unrevoke") else "revoked"
    _log(f"branch.{b._status}", "branch", b.id, summary=b.name)
    db.session.commit()
    return jsonify({"branch": b.public(with_token=True)})


@app.route("/api/admin/licenses", methods=["GET"])
@admin_required
def list_licenses():
    status = request.args.get("status")
    club_uuid = request.args.get("clubUuid")
    q = (request.args.get("q") or "").strip().lower()
    rows = License.query.order_by(License.id.desc()).all()
    if club_uuid:
        rows = [l for l in rows if l.club and l.club.uuid == club_uuid]
    if status:
        rows = [l for l in rows if l.status == status]
    if q:
        rows = [l for l in rows if (l.club and (q in l.club.club_name.lower()
                or q in l.club.email.lower() or q in l.club.uuid.lower()))
                or q in l.activation_code.lower()]
    items, meta = _paginate(rows)
    return jsonify({"items": [l.public(with_club=True) for l in items], **meta})


@app.route("/api/admin/licenses/<int:lid>/revoke", methods=["POST"])
@admin_required
def revoke_license(lid):
    lic = db.session.get(License, lid)
    if not lic:
        return jsonify({"error": "License not found."}), 404
    lic._status = "revoked"
    _log("license.revoke", "license", lic.id, summary=f"License revoked for {lic.club.club_name}",
         clubUuid=lic.club.uuid)
    db.session.commit()
    return jsonify(lic.public(with_club=True))


@app.route("/api/admin/licenses/<int:lid>/unrevoke", methods=["POST"])
@admin_required
def unrevoke_license(lid):
    lic = db.session.get(License, lid)
    if not lic:
        return jsonify({"error": "License not found."}), 404
    lic._status = "active"   # derived status may still read 'expired' if past expiry
    _log("license.unrevoke", "license", lic.id, summary=f"License restored for {lic.club.club_name}",
         clubUuid=lic.club.uuid)
    db.session.commit()
    return jsonify(lic.public(with_club=True))


@app.route("/api/admin/licenses/<int:lid>/renew", methods=["POST"])
@admin_required
def renew_license(lid):
    lic = db.session.get(License, lid)
    if not lic:
        return jsonify({"error": "License not found."}), 404
    days = int((request.json or {}).get("days", 365))
    base = _utcnow()
    cur = _naive(lic.expires_at)
    # Extend from the later of now / current expiry, unless it was revoked.
    start = max(base, cur) if (cur and lic._status != "revoked") else base
    lic.expires_at = start + dt.timedelta(days=days)
    try:
        _prev = signing.inspect(lic.token)
        _mods = _prev.get("ent", [])
        _branches = _prev.get("branches", 1)
    except Exception:
        _mods, _branches = [], 1
    lic.token = signing.mint(lic.club.uuid, lic.club.club_name,
                             max(1, (lic.expires_at - base).days), lic.device_list, _mods, _branches)
    lic._status = "active"
    _log("license.renew", "license", lic.id, summary=f"License renewed +{days}d for {lic.club.club_name}",
         clubUuid=lic.club.uuid, days=days)
    db.session.commit()
    return jsonify(lic.public(with_token=True, with_club=True))


# ── admin: audit ─────────────────────────────────────────────────────────────

@app.route("/api/admin/events", methods=["GET"])
@admin_required
def list_events():
    rows = AdminEvent.query.order_by(AdminEvent.id.desc()).all()
    items, meta = _paginate(rows)
    return jsonify({"items": [e.public() for e in items], **meta})


# ── online activation (called by the app with uuid+code) ─────────────────────

@app.route("/license/<club_uuid>", methods=["GET"])
def fetch_license(club_uuid):
    now = _utcnow()
    lic = (License.query.join(Club).filter(
        Club.uuid == club_uuid, Club.is_active.is_(True),
        License.activation_code == request.args.get("code", ""),
        License._status != "revoked", License.expires_at > now)
        .order_by(License.id.desc()).first())
    if not lic:
        return jsonify({"error": "No active license for that ID and code."}), 404
    return jsonify({"token": lic.token})


@app.route("/license/<club_uuid>/heartbeat", methods=["POST"])
def license_heartbeat(club_uuid):
    """Called periodically by an activated install to confirm its license is
    still valid. Auth is possession of the token itself, so even offline /
    file-activated installs are revocable. Returns the current token so a
    vendor renewal / re-issue propagates on the next beat."""
    club = Club.query.filter_by(uuid=club_uuid).first()
    if not club:
        return jsonify({"valid": False, "status": "unknown", "reason": "unknown"})
    if not club.is_active:
        return jsonify({"valid": False, "status": "suspended", "reason": "suspended"})
    lic = License.query.filter_by(club_id=club.id).order_by(License.id.desc()).first()
    if not lic:
        return jsonify({"valid": False, "status": "no_license", "reason": "no_license"})
    st = lic.status                         # active | expired | revoked (derived)
    valid = (st == "active")
    return jsonify({
        "valid": valid,
        "status": st,
        "reason": None if valid else st,
        "expiresAt": _iso(lic.expires_at),
        "token": lic.token if valid else None,
    })


# ── Per-branch heartbeat: lets an install confirm a branch is still licensed
#    and detect per-branch revocation (independent of siblings). ──
@app.route("/license/branch/<branch_uid>/heartbeat", methods=["POST"])
def branch_heartbeat(branch_uid):
    b = Branch.query.filter_by(uid=branch_uid).first()
    if not b:
        return jsonify({"valid": False, "status": "unknown", "reason": "unknown"})
    st = b.status                                   # active | revoked | archived | expired
    valid = (st == "active")
    return jsonify({"valid": valid, "status": st,
                    "reason": None if valid else st,
                    "token": b.token if valid else None})


# ── Owner-facing branch management (from the app's Manage License page).
#    The owner is authenticated with their club session (club_required). ──
@app.route("/api/club/branches", methods=["GET", "POST"])
@club_required
def club_branches():
    club = g.club
    if request.method == "GET":
        return jsonify({"branches": [b.public(with_token=True) for b in club.branches
                                     if b._status != "archived"],
                        "count": len([b for b in club.branches if b._status != "archived"])})
    b, err = _do_register_branch(club, request.get_json(silent=True) or {})
    if err:
        return err
    return jsonify({"branch": b.public(with_token=True)}), 201


@app.route("/api/club/branches/<int:bid>", methods=["DELETE"])
@club_required
def club_archive_branch(bid):
    b = db.session.get(Branch, bid)
    if not b or b.club_id != g.club.id:
        return jsonify({"error": "No such branch."}), 404
    b._status = "archived"                          # frees a licence slot
    _log("branch.archive", "branch", b.id, summary=b.name, clubUuid=g.club.uuid)
    db.session.commit()
    return jsonify({"ok": True})


# ── Club logo, hosted + served by the license server (survives app logout /
#    reinstall / device change — one file per club, keyed by uuid). ──
LOGO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "club_logos")
os.makedirs(LOGO_DIR, exist_ok=True)
_ALLOWED_LOGO_EXT = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


@app.route("/api/club/logo", methods=["POST"])
@club_required
def upload_club_logo():
    if "logo" not in request.files or request.files["logo"].filename == "":
        return jsonify({"error": "No file provided."}), 400
    f = request.files["logo"]
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "png"
    if ext not in _ALLOWED_LOGO_EXT:
        return jsonify({"error": "Unsupported image type."}), 400
    for old in glob.glob(os.path.join(LOGO_DIR, f"{g.club.uuid}.*")):
        try:
            os.remove(old)
        except OSError:
            pass
    f.save(os.path.join(LOGO_DIR, f"{g.club.uuid}.{ext}"))
    _log("club.logo", "club", g.club.id, summary=g.club.club_name)
    return jsonify({"logoUrl": f"/branding/{g.club.uuid}/logo"})


@app.route("/api/club/logo", methods=["DELETE"])
@club_required
def delete_club_logo():
    for old in glob.glob(os.path.join(LOGO_DIR, f"{g.club.uuid}.*")):
        try:
            os.remove(old)
        except OSError:
            pass
    return jsonify({"ok": True})


@app.route("/license/<club_uuid>/logo", methods=["POST"])
def token_upload_logo(club_uuid):
    """Logo upload authenticated by the club's signed LICENCE token (the app
    holds this, not a club web session). Lets an install back its logo up to
    the server so it survives a reinstall / new device."""
    club = Club.query.filter_by(uuid=club_uuid).first()
    if not club:
        return jsonify({"error": "Unknown club."}), 404
    try:
        claims = signing.peek(request.form.get("token", ""))
    except Exception:
        claims = {}
    if claims.get("sub") != club_uuid:
        return jsonify({"error": "Token does not match this club."}), 403
    if "logo" not in request.files or request.files["logo"].filename == "":
        return jsonify({"error": "No file provided."}), 400
    f = request.files["logo"]
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "png"
    if ext not in _ALLOWED_LOGO_EXT:
        return jsonify({"error": "Unsupported image type."}), 400
    for old in glob.glob(os.path.join(LOGO_DIR, f"{club_uuid}.*")):
        try:
            os.remove(old)
        except OSError:
            pass
    f.save(os.path.join(LOGO_DIR, f"{club_uuid}.{ext}"))
    _log("club.logo", "club", club.id, summary=club.club_name)
    return jsonify({"logoUrl": f"/branding/{club_uuid}/logo"})


@app.route("/branding/<club_uuid>/logo", methods=["GET"])
def serve_club_logo(club_uuid):
    """Public: the club logo shown on the app's login gate + customer surfaces."""
    matches = glob.glob(os.path.join(LOGO_DIR, f"{club_uuid}.*"))
    if not matches:
        return jsonify({"error": "No logo set."}), 404
    return send_from_directory(LOGO_DIR, os.path.basename(matches[0]))


@app.route("/healthz")
def healthz():
    return jsonify({"ok": True})


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    if path.startswith("admin/"):
        path = path[len("admin/"):]
    full = os.path.join(DIST_DIR, path)
    if path and os.path.isfile(full):
        return send_from_directory(DIST_DIR, path)
    if not os.path.isfile(os.path.join(DIST_DIR, "index.html")):
        return "Frontend build not found. Run 'npm run build' in the frontend directory.", 404
    return send_from_directory(DIST_DIR, "index.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Baize licensing server.")
    parser.add_argument("--dev", action="store_true", help="Run using the Flask development server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8090)), help="Port number")
    args = parser.parse_args()

    if args.dev:
        print(f"Starting DEV server on {args.host}:{args.port}...")
        app.run(host=args.host, port=args.port, debug=True)
    else:
        print(f"Starting PRODUCTION server on {args.host}:{args.port}...")
        try:
            # Unix / Linux / macOS (Gunicorn)
            from gunicorn.app.base import BaseApplication

            class StandaloneApplication(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            options = {
                "bind": f"{args.host}:{args.port}",
                "workers": int(os.environ.get("WEB_CONCURRENCY", 4)),
                "loglevel": "info",
            }
            StandaloneApplication(app, options).run()

        except ImportError:
            # Fallback for Windows or systems without Gunicorn (Waitress)
            try:
                from waitress import serve
                serve(app, host=args.host, port=args.port)
            except ImportError:
                print("Production WSGI server (gunicorn/waitress) not installed. Falling back to Flask dev server...")
                app.run(host=args.host, port=args.port)