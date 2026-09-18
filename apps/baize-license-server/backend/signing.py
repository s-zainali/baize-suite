"""Ed25519 signing/verification — the one place crypto lives (CLI + web both use it)."""
import datetime as dt
import json
import os

import jwt
from cryptography.hazmat.primitives import serialization as ser
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ISSUER = "baize"
ALGO = "EdDSA"
KID = os.environ.get("LICENSE_KID", "baize-1")   # must match the app's LICENSE_KID
HERE = os.path.dirname(os.path.abspath(__file__))
PRIV_PATH = os.environ.get("LICENSE_PRIVATE_KEY_FILE", os.path.join(HERE, ".private_key.pem"))
PUB_PATH = os.environ.get("LICENSE_PUBLIC_KEY_FILE", os.path.join(HERE, ".public_key.pem"))


def keygen(force=False):
    if os.path.exists(PRIV_PATH) and not force:
        raise SystemExit(f"{PRIV_PATH} exists. Use force=True to overwrite "
                         "(this invalidates every license already issued).")
    priv = Ed25519PrivateKey.generate()
    open(PRIV_PATH, "w").write(priv.private_bytes(
        ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()).decode())
    os.chmod(PRIV_PATH, 0o600)
    pub = priv.public_key().public_bytes(
        ser.Encoding.PEM, ser.PublicFormat.SubjectPublicKeyInfo).decode()
    open(PUB_PATH, "w").write(pub)
    return pub


def _private():
    key = os.environ.get("LICENSE_PRIVATE_KEY")
    if key:
        return key
    if not os.path.exists(PRIV_PATH):
        raise SystemExit(f"No private key at {PRIV_PATH} and LICENSE_PRIVATE_KEY unset. Run keygen.")
    return open(PRIV_PATH).read()


def mint(sub, club, days, devices, modules=None, branches=1, branch=None):
    """Sign a license token for a club. `devices` is a list of fingerprints
    (empty = unbound). Claims match exactly what the Baize app verifies."""
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "iss": ISSUER, "sub": sub, "club": club,
        "iat": now, "exp": now + dt.timedelta(days=int(days)),
        "ver": 1, "sys": list(devices or []),
        "ent": list(modules or []),   # licensed add-on module keys
        "branches": int(branches or 1),   # how many branches the club may run
        **({"branch": branch} if branch else {}),   # per-branch token: which child branch
    }
    return jwt.encode(payload, _private(), algorithm=ALGO, headers={"kid": KID})


def inspect(token):
    return jwt.decode(token, options={"verify_signature": False})