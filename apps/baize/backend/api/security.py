"""
Password hashing — Argon2id, with transparent migration off legacy hashes.

New passwords are hashed with Argon2id (OWASP's first recommendation: memory-hard,
so GPU/ASIC cracking is far harder than PBKDF2). Existing accounts were stored
with Werkzeug's PBKDF2; verify_password still accepts those and hands back a fresh
Argon2 hash so the caller can upgrade the row in place on next login. Nobody gets
locked out; everyone drifts onto Argon2 as they sign in.
"""
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from werkzeug.security import check_password_hash

_ph = PasswordHasher()   # sane Argon2id defaults


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(stored: str, password: str):
    """Return (ok, upgraded_hash_or_None).

    upgraded_hash is set when the stored hash is a legacy (PBKDF2/scrypt) one
    that verified, or an Argon2 hash whose parameters are now out of date — in
    both cases the caller should persist it.
    """
    if not stored:
        return False, None
    if stored.startswith("$argon2"):
        try:
            _ph.verify(stored, password)
        except Argon2Error:
            return False, None
        return True, (_ph.hash(password) if _ph.check_needs_rehash(stored) else None)
    # legacy Werkzeug hash ("pbkdf2:...", "scrypt:...")
    if check_password_hash(stored, password):
        return True, hash_password(password)   # migrate to Argon2
    return False, None