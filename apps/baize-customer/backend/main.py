"""
baize-customer API (FastAPI) — the standalone customer bookings backend.

Serves the customer app: browse a club's branches, see live table availability,
and book a table. Writes bookings into the shared (cloud) DB that club installs
pull from via sync. Routes are mounted under /customer to match the frontend's
VITE_API_URL/customer base.
"""
import os
import uuid
import datetime as dt
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Boolean,
                        Text, ForeignKey, func, or_)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
JWT_SECRET = os.environ.get("CUSTOMER_JWT_SECRET", "dev-customer-secret")
CLUB_UID = os.environ.get("CLUB_UID")          # scope to one club; None = all (dev)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()
ph = PasswordHasher()

app = FastAPI(title="baize-customer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"], # Your Vue dev server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── models (subset of the shared schema needed for bookings) ──
class Branch(Base):
    __tablename__ = "branch"
    id = Column(Integer, primary_key=True)
    uid = Column(String); name = Column(String); address = Column(String)
    status = Column(String); club_uid = Column(String); deleted_at = Column(DateTime)

class Lounge(Base):
    __tablename__ = "lounge"
    id = Column(Integer, primary_key=True)
    uid = Column(String); name = Column(String); status = Column(String)
    sort_order = Column(Integer); branch_id = Column(Integer); club_uid = Column(String); deleted_at = Column(DateTime)

class PoolTable(Base):
    __tablename__ = "pool_table"
    id = Column(Integer, primary_key=True)
    uid = Column(String); table_id = Column(String); table_type = Column(String)
    is_active = Column(Boolean); lounge_uid = Column(String); sort_order = Column(Integer)
    branch_id = Column(Integer); club_uid = Column(String); status = Column(String); deleted_at = Column(DateTime)

class TableType(Base):
    __tablename__ = "table_type"
    id = Column(Integer, primary_key=True)
    key = Column(String); label = Column(String); color = Column(String)
    renderer = Column(String); badge = Column(String); sort_order = Column(Integer)

class GlobalRate(Base):
    __tablename__ = "global_rate"
    id = Column(Integer, primary_key=True)
    table_type = Column(String); weekday_rate = Column(Integer); weekend_rate = Column(Integer)
    branch_id = Column(Integer); club_uid = Column(String)

class Booking(Base):
    __tablename__ = "booking"
    id = Column(Integer, primary_key=True)
    sync_id = Column(String, default=lambda: str(uuid.uuid4()))
    branch_id = Column(Integer); club_uid = Column(String)
    code = Column(String); table_uid = Column(String); table_type = Column(String)
    table_number = Column(Integer); guest_name = Column(String); phone = Column(String)
    start_time = Column(DateTime); end_time = Column(DateTime); status = Column(String, default="booked")
    customer_id = Column(Integer); created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
    deleted_at = Column(DateTime)

class Customer(Base):
    __tablename__ = "customer"
    id = Column(Integer, primary_key=True)
    sync_id = Column(String, default=lambda: str(uuid.uuid4()))
    name = Column(String); phone = Column(String, index=True); email = Column(String)
    password_hash = Column(String); club_uid = Column(String)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


def db() -> Session:
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def _club(q, Model):
    return q.filter(Model.club_uid == CLUB_UID) if CLUB_UID else q


def current_customer(authorization: str = Header(None), s: Session = Depends(db)) -> Customer:
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


# ── auth ──
class SignUp(BaseModel):
    name: str; phone: str; email: Optional[str] = None; password: str
class SignIn(BaseModel):
    phone: str; password: str

def _token(c: Customer) -> str:
    return jwt.encode({"sub": str(c.id), "phone": c.phone}, JWT_SECRET, algorithm="HS256")

@app.post("/customer/register")
def register(body: SignUp, s: Session = Depends(db)):
    if s.query(Customer).filter(Customer.phone == body.phone).first():
        raise HTTPException(409, "That phone is already registered.")
    c = Customer(name=body.name, phone=body.phone, email=body.email,
                 password_hash=ph.hash(body.password), club_uid=CLUB_UID)
    s.add(c); s.commit()
    return {"token": _token(c), "profile": {"name": c.name, "phone": c.phone, "email": c.email}}

@app.post("/customer/login")
def login(body: SignIn, s: Session = Depends(db)):
    c = s.query(Customer).filter(Customer.phone == body.phone).first()
    try:
        if not c or not ph.verify(c.password_hash, body.password):
            raise ValueError
    except (VerifyMismatchError, ValueError):
        raise HTTPException(401, "Wrong phone or password.")
    return {"token": _token(c), "profile": {"name": c.name, "phone": c.phone, "email": c.email}}

@app.get("/customer/me")
def me(c: Customer = Depends(current_customer)):
    return {"profile": {"name": c.name, "phone": c.phone, "email": c.email}}


# ── booking flow ──
@app.get("/customer/table-types")
def table_types(s: Session = Depends(db)):
    return [{"key": t.key, "id": t.key, "value": t.key, "label": t.label, "color": t.color,
             "renderer": t.renderer, "badge": t.badge, "sortOrder": t.sort_order}
            for t in s.query(TableType).order_by(TableType.sort_order).all()]

@app.get("/customer/clubs")
def clubs(s: Session = Depends(db)):
    rows = s.query(Branch.club_uid).filter(Branch.deleted_at.is_(None)).distinct().all()
    return [{"uid": r[0]} for r in rows if r[0]]

@app.get("/customer/availability")
def availability(date: Optional[str] = None, branch: Optional[str] = None, s: Session = Depends(db)):
    day = dt.date.fromisoformat(date) if date else dt.date.today()
    start = dt.datetime.combine(day, dt.time.min); end = start + dt.timedelta(days=1)
    weekend = day.weekday() >= 5

    branches = _club(s.query(Branch).filter(Branch.deleted_at.is_(None)), Branch)\
        .order_by(Branch.id).all()
    chosen = next((b for b in branches if b.uid == branch), None)
    if chosen is None and len(branches) == 1:
        chosen = branches[0]
    if chosen is None:
        return {"date": day.isoformat(),
                "branches": [{"uid": b.uid, "name": b.name} for b in branches],
                "selectedBranch": None, "lounges": [], "tables": [], "busy": []}

    lounges = s.query(Lounge).filter(Lounge.status != "deleted", Lounge.branch_id == chosen.id).all()
    tables = s.query(PoolTable).filter(PoolTable.status != "deleted", PoolTable.branch_id == chosen.id)\
        .order_by(PoolTable.sort_order).all()
    rates = {r.table_type: r for r in s.query(GlobalRate).filter(
        or_(GlobalRate.branch_id == chosen.id, GlobalRate.branch_id.is_(None))).all()}
    busy = s.query(Booking).filter(Booking.branch_id == chosen.id,
                                   Booking.status.in_(["booked", "active"]),
                                   Booking.start_time < end, Booking.end_time > start,
                                   Booking.deleted_at.is_(None)).all()

    def rate_for(tt):
        r = rates.get(tt)
        return (r.weekend_rate if weekend else r.weekday_rate) if r else 0

    return {
        "date": day.isoformat(),
        "branches": [{"uid": b.uid, "name": b.name} for b in branches],
        "selectedBranch": chosen.uid,
        "lounges": [{"uid": lo.uid, "name": lo.name} for lo in lounges],
        "tables": [{"uid": t.uid, "id": t.table_id, "type": t.table_type, "loungeUid": t.lounge_uid,
                    "isActive": bool(t.is_active), "currentRate": rate_for(t.table_type)} for t in tables],
        "busy": [{"tableUid": b.table_uid, "startTime": b.start_time.isoformat(),
                  "endTime": b.end_time.isoformat()} for b in busy],
    }


class BookingIn(BaseModel):
    tableUid: str
    startTime: str
    endTime: str

@app.post("/customer/bookings")
def create_booking(body: BookingIn, c: Customer = Depends(current_customer), s: Session = Depends(db)):
    table = s.query(PoolTable).filter(PoolTable.uid == body.tableUid, PoolTable.status != "deleted").first()
    if not table:
        raise HTTPException(404, "That table doesn't exist.")
    start = dt.datetime.fromisoformat(body.startTime); end = dt.datetime.fromisoformat(body.endTime)
    if end <= start:
        raise HTTPException(400, "End time must be after the start.")
    clash = s.query(Booking).filter(Booking.table_uid == table.uid,
                                    Booking.status.in_(["booked", "active"]),
                                    Booking.start_time < end, Booking.end_time > start,
                                    Booking.deleted_at.is_(None)).first()
    if clash:
        raise HTTPException(409, "That slot was just taken.")
    b = Booking(branch_id=table.branch_id, club_uid=table.club_uid, table_uid=table.uid,
                table_type=table.table_type, guest_name=c.name, phone=c.phone,
                start_time=start, end_time=end, status="booked", customer_id=c.id,
                code=str(uuid.uuid4())[:6].upper())
    s.add(b); s.commit()
    return {"ok": True, "code": b.code, "booking": {"tableUid": b.table_uid,
            "startTime": start.isoformat(), "endTime": end.isoformat()}}


@app.get("/")
def root():
    return {"service": "baize-customer", "ok": True}