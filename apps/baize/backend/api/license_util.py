"""
License verification for the Baize app.

A license is an Ed25519-signed JWT minted by the vendor's license authority
(license-server/baize_license.py). The app holds only the PUBLIC key, so it can
verify a license entirely offline — which is what makes file/paste activation
work with no internet. The public key is not a secret; the private key never
leaves the vendor.

Device binding: the token carries `sys`, a LIST of enrolled device fingerprints.
Each fingerprint is this machine's salted, per-component hashes (never the raw
hardware serials). A device is accepted if it matches an enrolled fingerprint on
all-but-one component (N-of-M), so a single part swap doesn't lock a club out.

Pinning algorithms=["EdDSA"] blocks the "alg: none" / HMAC-confusion downgrades.
"""
import functools
import hashlib
import json
import urllib.request
import urllib.error
import os
import platform
import subprocess
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

from models import db, License, Branch, BranchLicense
from cryptography.hazmat.primitives.serialization import load_pem_public_key

load_dotenv()

LICENSE_ISSUER = "baize"
LICENSE_ALGO = "EdDSA"

# DEMO public key — matches the license tool's keypair. Before production run
# `python baize_license.py keygen` and replace this (or set LICENSE_PUBLIC_KEY).
_DEFAULT_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAyeJP+REYpATlyV+AAd/XEFLLdJicLOjnpEZhegQd7/U=
-----END PUBLIC KEY-----
"""


# Load your hardcoded keys properly so PyJWT accepts EdDSA
_DEFAULT_PUBLIC_KEY_OBJ = load_pem_public_key(_DEFAULT_PUBLIC_KEY.encode('utf-8'))

raw_env_key = os.environ.get("LICENSE_PUBLIC_KEY")

if raw_env_key:
    PUBLIC_KEY = load_pem_public_key(raw_env_key.strip().encode('utf-8'))
else:
    PUBLIC_KEY = _DEFAULT_PUBLIC_KEY_OBJ
# Keys addressable by the token header's `kid`, so a key can be rotated in later
# without invalidating tokens signed by the old one. Unknown/absent kid falls
# back to the current key.
CURRENT_KID = os.environ.get("LICENSE_KID", "baize-1")
PUBLIC_KEYS = {CURRENT_KID: PUBLIC_KEY}

# Obscures raw hardware serials in the fingerprint; NOT a secret (it ships in the
# app). Its only job is to keep plain serials out of tokens/logs and off the
# shelf for rainbow tables.
_FP_SALT = os.environ.get("LICENSE_FP_SALT", "baize.fp.v1$do-not-rely-on-secrecy")

# When on, the backend refuses data routes without a valid license (see index.py).
# Enforcement is NOT configurable. The app is never usable without a valid,
# server-verified license — baked in so no env var / run flag can disable it.
# The real teeth live in the before_request guard in index.py.
ENFORCE = True

# Device binding ties a license to specific hardware. Turn it OFF for the
# cloud/online build (Render), where the "device" is an ephemeral container
# with no fixed fingerprint: set DEVICE_BINDING=off there.
DEVICE_BINDING = os.environ.get("DEVICE_BINDING", "on").lower() not in ("off", "0", "false", "no")

# Heartbeat: an activated install periodically re-checks with the license
# server so a revoked/suspended/renewed license takes effect without a restart.
# BAKED IN — deliberately NOT read from env. These are security-critical: a
# local operator could otherwise unset the server URL to kill the heartbeat
# (dodging revocation) or set a huge grace to run a revoked license forever.
# Change LICENSE_SERVER_URL to your license server and rebuild.
LICENSE_SERVER_URL = "https://baize-license-server.onrender.com".rstrip("/")   # <-- SET TO YOUR LICENSE SERVER
HEARTBEAT_INTERVAL = 60        # seconds between server beats
HEARTBEAT_GRACE = 259200       # 72h unreachable, then gate — cannot be extended via env


class LicenseError(Exception):
    pass


# ── device fingerprint ───────────────────────────────────────────────────────

def _raw_components():
    """Best-effort stable hardware identifiers for THIS machine, as a list."""
    components = []
    system = platform.system()
    try:
        if _is_wsl():
            for ps in ("(Get-CimInstance Win32_ComputerSystemProduct).UUID",
                       "(Get-CimInstance Win32_BaseBoard).SerialNumber"):
                r = subprocess.run(["powershell.exe", "-Command", ps],
                                   capture_output=True, text=True, timeout=5)
                if r.returncode == 0 and r.stdout.strip():
                    components.append(r.stdout.strip())
        elif system == "Windows":
            r = subprocess.run(["wmic", "csproduct", "get", "uuid"],
                               capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split("\n")
            if len(lines) > 1:
                components.append(lines[1].strip())
        elif system == "Linux":
            if os.path.exists("/etc/machine-id"):
                components.append(open("/etc/machine-id").read().strip())
        elif system == "Darwin":
            r = subprocess.run(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                               capture_output=True, text=True, timeout=5)
            for line in r.stdout.split("\n"):
                if "IOPlatformUUID" in line:
                    components.append(line.split('"')[-2])
    except Exception:
        pass
    try:
        components.append(hex(uuid.getnode()))   # MAC — least stable, so it's just one vote
    except Exception:
        pass
    return [c for c in components if c]


def _is_wsl():
    if platform.system() != "Linux":
        return False
    try:
        return "microsoft" in open("/proc/version").read().lower()
    except Exception:
        return False


@functools.lru_cache(maxsize=1)
def device_fingerprint():
    """Salted per-component hashes for this machine, joined by '.'.

    Cached for the life of the process: the raw gather shells out, so recomputing
    it on every license check (which happens per-request under enforcement) would
    be a real performance problem.
    """
    hashed = sorted(
        hashlib.sha256((_FP_SALT + c).encode()).hexdigest()[:16]
        for c in _raw_components()
    )
    return ".".join(hashed)


def _device_ok(sys_claim):
    """True if this machine matches an enrolled device (or the license is unbound)."""
    if not sys_claim:                 # empty list → not device-locked (online tier)
        return True
    devices = sys_claim if isinstance(sys_claim, list) else [sys_claim]
    local = {h for h in device_fingerprint().split(".") if h}
    for dev in devices:
        enrolled = {h for h in str(dev).split(".") if h}
        if not enrolled:
            continue
        need = max(1, len(enrolled) - 1)   # tolerate one drifted component
        if len(local & enrolled) >= need:
            return True
    return False


# ── token verification ───────────────────────────────────────────────────────

def _key_for(token):
    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except jwt.InvalidTokenError:
        kid = None
    return PUBLIC_KEYS.get(kid, PUBLIC_KEY)


def verify_token(token):
    """Return the claims of a valid token for THIS device, or raise LicenseError."""
    try:
        claims = jwt.decode(
            token,
            _key_for(token),
            algorithms=[LICENSE_ALGO],
            issuer=LICENSE_ISSUER,
            options={"require": ["exp", "iat", "sub", "club", "sys"]},
        )
    except jwt.ExpiredSignatureError:
        raise LicenseError("This license has expired.")
    except jwt.InvalidIssuerError:
        raise LicenseError("License was not issued for this product.")
    except jwt.InvalidTokenError:
        raise LicenseError("Invalid or tampered license token.")

    if DEVICE_BINDING and not _device_ok(claims.get("sys")):
        raise LicenseError("This license is bound to a different device.")
    return claims


# ── clock-rollback guard ─────────────────────────────────────────────────────

def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _naive(v):
    return v.replace(tzinfo=None) if (v and v.tzinfo is not None) else v


def _is_expired(lic):
    return bool(lic.expires_at) and _utcnow() > _naive(lic.expires_at)


def _grace_left_seconds(lic):
    if not lic.expires_at:
        return 0
    return max(0, HEARTBEAT_GRACE - (_utcnow() - _naive(lic.expires_at)).total_seconds())


def _clock_rolled_back(lic):
    # A day of slack absorbs timezone/NTP jitter; anything beyond means the clock
    # was set back (the offline trick to revive an expired license).
    return bool(lic.last_seen_at) and (_utcnow() + timedelta(days=1) < lic.last_seen_at)


def _touch_last_seen(lic):
    now = _utcnow()
    if not lic.last_seen_at or now - lic.last_seen_at > timedelta(hours=1):
        lic.last_seen_at = now
        db.session.commit()


# ── public API ───────────────────────────────────────────────────────────────

def active_license():
    return License.query.order_by(License.id.desc()).first()


def _reason_text(status):
    return {
        "revoked": "This license has been revoked.",
        "suspended": "This club's account has been suspended.",
        "expired": "This license has expired.",
        "no_license": "No active license found for this club.",
        "unknown": "This license is not recognised by the server.",
    }.get(status, "This license is no longer valid.")


def _heartbeat(lic):
    """Throttled beat to the license server. Returns 'valid' | 'revoked' |
    'unreachable'. Authenticates with the stored token (so offline installs are
    revocable), stamps server_status/server_checked_at, sets revoked_at (sticky)
    on a revoke, and adopts a newer token the server hands back (renewal pickup)."""
    now = _utcnow()
    # Throttle: real network call at most once per HEARTBEAT_INTERVAL; otherwise
    # answer from the cached verdict (is_licensed runs on every request).
    if lic.server_checked_at and (now - lic.server_checked_at) < timedelta(seconds=HEARTBEAT_INTERVAL):
        return "revoked" if lic.server_status in ("revoked", "suspended") else "valid"
    try:
        req = urllib.request.Request(
            f"{LICENSE_SERVER_URL}/license/{lic.club_uid}/heartbeat",
            data=json.dumps({"token": lic.token}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        return "unreachable"

    print('Checking license')
    lic.server_checked_at = now
    if data.get("valid"):
        lic.server_status = "active"
        lic.revoked_at = None
        new_token = data.get("token")
        if new_token and new_token != lic.token:
            try:                                   # only adopt a token valid for THIS device
                claims = verify_token(new_token)
                lic.token = new_token
                lic.issued_at = datetime.fromtimestamp(claims["iat"], timezone.utc).replace(tzinfo=None)
                lic.expires_at = datetime.fromtimestamp(claims["exp"], timezone.utc).replace(tzinfo=None)
                lic.system_identifier = json.dumps(claims.get("sys") or [])
                lic.entitlements = json.dumps(claims.get("ent") or [])
            except LicenseError:
                pass
        db.session.commit()
        return "valid"

    reason = data.get("reason") or "revoked"
    lic.server_status = reason
    if reason in ("revoked", "suspended"):
        lic.revoked_at = now                       # sticky hard-stop — revoke is never graced
        db.session.commit()
        return "revoked"
    # expired / no_license / unknown: NOT a revoke — let local expiry + grace decide
    db.session.commit()
    return "expired"


def _effective_valid(lic):
    """(valid, reason). Order of authority:
      1. Revoked / suspended  → hard stop, immediately. Never graced.
      2. Live heartbeat revoke → hard stop, immediately.
      3. Crypto / device / clock → instant fail on tamper or wrong device.
      4. Expiry ALONE           → the grace window (keep running up to
         HEARTBEAT_GRACE past expiry, then lock).
    Being unable to reach the server is NOT fatal on its own — an in-term
    license keeps working offline; only expiry (and revocation) gate."""
    # 1 + 2: revocation is absolute.
    if lic.revoked_at:
        return False, _reason_text(lic.server_status)
    if LICENSE_SERVER_URL:
        if _heartbeat(lic) == "revoked":
            return False, _reason_text(lic.server_status)
    # 3 + 4: local crypto, with expiry handled by the grace window.
    try:
        verify_token(lic.token)
    except LicenseError as e:
        if _is_expired(lic):
            if _grace_left_seconds(lic) > 0:
                return True, "grace"          # expired but inside the grace window
            return False, "This license has expired."
        return False, str(e)                  # tampered / wrong device / issuer → instant
    if _clock_rolled_back(lic):
        return False, "The system clock appears to have been set back."
    return True, None


def is_licensed():
    """True only if the stored license passes the offline check AND the server
    (when configured) hasn't revoked/suspended it beyond the grace window."""
    # Branch-only model: the install is licensed if ANY registered branch
    # carries a valid, server-issued branch licence. (There is no club licence.)
    try:
        for bl in BranchLicense.query.all():
            if _branch_valid(bl):
                return True
    except Exception:
        pass
    return False


def _days_left(expires_at):
    if not expires_at:
        return None
    return max(0, (expires_at - _utcnow()).days)


BASE_MODULES = set()   # base station renderer is "pool" — always allowed, not gated here
ALL_MODULES = {"playstation", "xbox", "pc", "foosball", "canteen", "insights", "bookings", "payments"}


def _verified_token(token):
    """Signature-valid claims from a token (issuer + device checked), expiry
    ignored (grace decided separately). None on tamper/wrong-device. Shared by
    club AND branch entitlement derivation — the tamper-proof source."""
    if not token:
        return None
    try:
        claims = jwt.decode(
            token, _key_for(token), algorithms=[LICENSE_ALGO],
            issuer=LICENSE_ISSUER,
            options={"verify_exp": False, "require": ["iat", "sub", "club", "sys"]},
        )
    except jwt.InvalidTokenError as e:
        print("JWT DECODE FAILED:", type(e).__name__, str(e))
        return None
    if DEVICE_BINDING and not _device_ok(claims.get("sys")):
        return None
    return claims


def _verified_claims(lic):
    return _verified_token(lic.token) if lic else None


def licensed_features():
    """Licensed add-on modules for this install. Derived from the SIGNED token
    on every call — NOT from the `entitlements` DB column (which a client could
    edit to grant themselves paid modules). No features unless the licence is
    actually usable (valid or in grace). Base (pool) features aren't listed."""
    lic = active_license()
    if not lic or not is_licensed():           # revoked / expired-past-grace / unlicensed → base only
        return set()
    claims = _verified_claims(lic)
    if not claims:                              # tampered / wrong device
        return set()
    return set(claims.get("ent") or []) & ALL_MODULES


def has_feature(key):
    return key in licensed_features()


def _iso_utc(dt):
    """Serialize a naive-UTC datetime as an explicit-UTC ISO string (…+00:00),
    so the browser's new Date() parses it as UTC instead of local time."""
    if not dt:
        return None
    return dt.replace(tzinfo=timezone.utc).isoformat()


def licensed_branch_count():
    """How many branches this install's licence permits (default 1). Read from
    the signed token's `branches` claim; the token is already validated by
    is_licensed(), so an unverified decode is fine just to read the number."""
    lic = active_license()
    claims = _verified_claims(lic) if lic else None
    if not claims:
        return 1
    try:
        return max(1, int(claims.get("branches", 1) or 1))
    except Exception:
        return 1


def _grace_left_for(expires_at):
    if not expires_at:
        return HEARTBEAT_GRACE
    return max(0, HEARTBEAT_GRACE - (_utcnow() - _naive(expires_at)).total_seconds())


def store_branch_license(token, name=None):
    """Activate/renew a branch's license on this install. Verifies the signed
    token (must carry a `branch` claim) and upserts the local Branch row so
    scoping + the picker see it."""
    claims = verify_token(token)                 # signature + device + exp
    buid = claims.get("branch")
    if not buid:
        raise LicenseError("This token is not a branch license.")
    bl = BranchLicense.query.filter_by(branch_uid=buid).first()
    if bl is None:
        bl = BranchLicense(branch_uid=buid)
        db.session.add(bl)
    bl.club_uid = claims["sub"]
    bl.token = token
    bl.name = name or bl.name or "Branch"
    bl.issued_at = datetime.fromtimestamp(claims["iat"], timezone.utc).replace(tzinfo=None)
    bl.expires_at = datetime.fromtimestamp(claims["exp"], timezone.utc).replace(tzinfo=None)
    bl.entitlements = json.dumps(claims.get("ent") or [])
    bl.system_identifier = json.dumps(claims.get("sys") or [])
    bl.revoked_at = None
    bl.server_status = "active"
    bl.server_checked_at = None
    b = Branch.query.filter_by(uid=buid).first()
    if b is None:
        nxt = (db.session.query(db.func.max(Branch.sort_order)).scalar() or 0) + 1
        b = Branch(uid=buid, name=bl.name, status="active", is_default=False, sort_order=nxt)
        db.session.add(b)
    else:
        b.name = bl.name
        b.deleted_at = None
    db.session.commit()
    return bl


def active_branch_license(branch_uid):
    return BranchLicense.query.filter_by(branch_uid=branch_uid).first() if branch_uid else None


def _branch_heartbeat(bl):
    """Throttled beat for a branch license — detects per-branch revocation and
    adopts a renewed token the server hands back. Fails silently if the server
    (or its branch endpoint) is unreachable, so a branch keeps working offline."""
    if not LICENSE_SERVER_URL:
        return
    now = _utcnow()
    if bl.server_checked_at and (now - bl.server_checked_at) < timedelta(seconds=HEARTBEAT_INTERVAL):
        return
    try:
        req = urllib.request.Request(
            f"{LICENSE_SERVER_URL}/license/branch/{bl.branch_uid}/heartbeat",
            data=json.dumps({"token": bl.token}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
    except Exception:
        return
    bl.server_checked_at = now
    if data.get("valid"):
        bl.server_status = "active"
        bl.revoked_at = None
        new_token = data.get("token")
        if new_token and new_token != bl.token and _verified_token(new_token):
            try:
                c = verify_token(new_token)
                if c.get("branch") == bl.branch_uid:
                    bl.token = new_token
                    bl.expires_at = datetime.fromtimestamp(c["exp"], timezone.utc).replace(tzinfo=None)
                    bl.entitlements = json.dumps(c.get("ent") or [])
            except LicenseError:
                pass
    else:
        reason = data.get("reason") or "revoked"
        bl.server_status = reason
        if reason in ("revoked", "suspended", "archived"):
            bl.revoked_at = now                  # sticky per-branch hard stop
    db.session.commit()


def _branch_valid(bl):
    """Is this branch license usable? Revoked → no. Past expiry → only within
    grace. Otherwise yes. (Signature is checked in branch_features.)"""
    if not bl or bl.revoked_at:
        return False
    _branch_heartbeat(bl)
    if bl.revoked_at:
        return False
    if bl.expires_at and _utcnow() > _naive(bl.expires_at):
        return _grace_left_for(bl.expires_at) > 0
    return True


def branch_features(branch_uid):
    """Licensed add-on modules for ONE branch — signature-derived from that
    branch's own token, default-deny. Base (pool) features aren't listed."""
    bl = active_branch_license(branch_uid)
    if not bl or not _branch_valid(bl):
        return set()
    claims = _verified_token(bl.token)
    if not claims or claims.get("branch") != branch_uid:
        return set()
    return set(claims.get("ent") or []) & ALL_MODULES


def heartbeat_branches():
    """Beat every stored branch license (each throttled) so per-branch
    revocation/renewal propagates alongside the club heartbeat."""
    for bl in BranchLicense.query.all():
        try:
            _branch_valid(bl)
        except Exception:
            pass

def _local_logo_url(club_uid):
    try:
        import glob
        m = sorted(glob.glob(os.path.join(os.getcwd(), "uploads", f"logo_{club_uid}_*")))
        return f"/license/media/{os.path.basename(m[-1])}" if m else None
    except Exception:
        return None


def _branch_status():
    """Status for a BRANCH-based install (no club licence). The frontend gate
    reads `valid`/`activated` from here, so a freshly-activated branch lifts it."""
    bls = BranchLicense.query.all()
    if not bls:
        return {"activated": False, "valid": False, "state": "unlicensed", "enforced": ENFORCE,
                "clubName": None, "clubUid": None, "expiresAt": None, "daysLeft": None,
                "graceHoursLeft": None, "logoUrl": None, "deviceBinding": DEVICE_BINDING,
                "serverStatus": None, "lastServerCheck": None, "entitlements": [],
                "branchLimit": None, "reason": "No branch activated."}
    valid_bls = [b for b in bls if _branch_valid(b)]
    valid = bool(valid_bls)
    # Report the SELECTED branch (X-Branch) so the status + entitlements reflect
    # the branch the install is currently operating as — falling back to the
    # first valid one. This keeps the frontend's type registry in step.
    rep = None
    try:
        from flask import request, has_request_context
        if has_request_context():
            hdr = request.headers.get("X-Branch")
            if hdr and hdr.isdigit():
                lb = Branch.query.get(int(hdr))
                if lb:
                    rep = next((x for x in bls if x.branch_uid == lb.uid), None)
    except Exception:
        rep = None
    if rep is None:
        rep = valid_bls[0] if valid_bls else bls[0]
    dl = _days_left(rep.expires_at)
    if rep.revoked_at:
        state = rep.server_status if rep.server_status in ("revoked", "suspended") else "revoked"
    elif rep.expires_at and _utcnow() > _naive(rep.expires_at):
        state = "grace" if _grace_left_for(rep.expires_at) > 0 else "expired"
    elif not valid:
        state = "invalid"
    else:
        state = "expiring" if (dl is not None and dl <= 7) else "active"
    grace_hours = int((_grace_left_for(rep.expires_at) + 3599) // 3600) if state == "grace" else None
    return {
        "activated": True, "valid": valid, "state": state, "enforced": ENFORCE,
        "clubName": rep.name, "clubUid": rep.club_uid,
        "expiresAt": _iso_utc(rep.expires_at), "daysLeft": dl, "graceHoursLeft": grace_hours,
        "logoUrl": _local_logo_url(rep.club_uid), "deviceBinding": DEVICE_BINDING,
        "serverStatus": rep.server_status, "entitlements": sorted(branch_features(rep.branch_uid)),
        "branchLimit": None, "lastServerCheck": _iso_utc(rep.server_checked_at),
        "reason": None if valid else "Branch licence not valid.",
    }


def license_status():
    """Full status for the owner + the frontend gate. Branch-only: the install's
    state is derived entirely from its activated branch licences."""
    heartbeat_branches()                 # keep per-branch revocation/renewal fresh
    return _branch_status()
    # (legacy club-licence path below retained but unreachable)
    lic = active_license()
    if not lic:
        return _branch_status()
    valid, reason = _effective_valid(lic)
    dl = _days_left(lic.expires_at)
    if lic.revoked_at:
        state = lic.server_status if lic.server_status in ("revoked", "suspended") else "revoked"
    elif _is_expired(lic):
        # Expiry is authoritative for the label: a license past its expiry is
        # in grace (still running) or fully expired — never "expiring"/"active".
        state = "grace" if _grace_left_seconds(lic) > 0 else "expired"
    elif not valid:
        state = "invalid"
    else:
        state = "expiring" if (dl is not None and dl <= 7) else "active"
    grace_hours = int((_grace_left_seconds(lic) + 3599) // 3600) if state == "grace" else None
    return {
        "activated": True,
        "valid": valid,
        "state": state,
        "enforced": ENFORCE,
        "clubName": lic.club_name,
        "clubUid": lic.club_uid,
        "expiresAt": _iso_utc(lic.expires_at),
        "daysLeft": _days_left(lic.expires_at),
        "graceHoursLeft": grace_hours,
        "logoUrl": lic.logo_url,
        "deviceBinding": DEVICE_BINDING,
        "serverStatus": lic.server_status,
        "entitlements": sorted(licensed_features()),
        "branchLimit": licensed_branch_count(),
        "lastServerCheck": _iso_utc(lic.server_checked_at),
        "reason": reason,
    }


def clear_license():
    """Remove the stored license entirely so the install drops back to the
    activation gate (is_licensed() → False). Used by owner 'deactivate'."""
    License.query.delete()
    BranchLicense.query.delete()
    db.session.commit()


def store_license(token):
    """Verify a token for this device and persist it. Renewal keeps the logo."""
    claims = verify_token(token)   # raises LicenseError (incl. wrong-device) if bad
    lic = License.query.filter_by(club_uid=claims["sub"]).first()
    if lic is None:
        lic = License(club_uid=claims["sub"])
        db.session.add(lic)
    lic.token = token
    lic.club_name = claims["club"]
    lic.issued_at = datetime.fromtimestamp(claims["iat"], timezone.utc).replace(tzinfo=None)
    lic.expires_at = datetime.fromtimestamp(claims["exp"], timezone.utc).replace(tzinfo=None)
    lic.activated_at = _utcnow()
    lic.last_seen_at = _utcnow()   # reset the clock baseline on (re)activation
    lic.system_identifier = json.dumps(claims.get("sys") or [])
    lic.entitlements = json.dumps(claims.get("ent") or [])
    lic.revoked_at = None          # a fresh (re)activation clears any prior revoke
    lic.server_status = "active"
    lic.server_checked_at = None   # force a real beat on next check
    if not lic.logo_url:
        # A prior deactivate/logout dropped the License row but NOT the logo file.
        # Re-link the club's most recent logo so branding survives logout/login.
        try:
            import glob
            uploads = os.path.join(os.getcwd(), "uploads")
            matches = sorted(glob.glob(os.path.join(uploads, f"logo_{claims['sub']}_*")))
            if matches:
                lic.logo_url = f"/license/media/{os.path.basename(matches[-1])}"
        except Exception:
            pass
    if not lic.logo_url and LICENSE_SERVER_URL:
        # Fresh install / new device: pull the logo the club previously uploaded
        # from the licence server, cache it locally, and serve that (offline-safe).
        try:
            with urllib.request.urlopen(f"{LICENSE_SERVER_URL}/branding/{claims['sub']}/logo", timeout=5) as r:
                data = r.read()
                ctype = (r.headers.get("Content-Type", "image/png") or "").split(";")[0].strip()
                ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp",
                       "image/svg+xml": "svg", "image/gif": "gif"}.get(ctype, "png")
                uploads = os.path.join(os.getcwd(), "uploads")
                os.makedirs(uploads, exist_ok=True)
                fname = f"logo_{claims['sub']}_{int(datetime.now().timestamp())}.{ext}"
                with open(os.path.join(uploads, fname), "wb") as fh:
                    fh.write(data)
                lic.logo_url = f"/license/media/{fname}"
        except Exception:
            pass
    db.session.commit()
    return lic


if __name__ == "__main__":
    # Run on a club's machine to read its fingerprint for enrollment:
    #   python license_util.py
    print(device_fingerprint())