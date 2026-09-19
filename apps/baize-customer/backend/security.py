"""Password hashing + customer JWT + the auth dependency."""
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from config import JWT_SECRET
from database import get_db
from models import Customer

_ph = PasswordHasher()

def hash_password(pw: str) -> str:
    return _ph.hash(pw)

def verify_password(hashed: str, pw: str) -> bool:
    try:
        return _ph.verify(hashed, pw)
    except (VerifyMismatchError, Exception):
        return False

def make_token(c: Customer) -> str:
    return jwt.encode({"sub": str(c.id), "phone": c.phone}, JWT_SECRET, algorithm="HS256")

def current_customer(authorization: str = Header(None), s: Session = Depends(get_db)) -> Customer:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in required.")
    try:
        claims = jwt.decode(authorization[7:], JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Session expired.")
    c = s.get(Customer, int(claims.get("sub", 0)))
    if not c:
        raise HTTPException(401, "Unknown customer.")
    return c
