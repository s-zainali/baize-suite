"""SQLAlchemy models — the subset of the shared schema this app reads/writes.
(Matches the club app's tables, including the sync columns.)"""
import uuid
import datetime as dt
from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint, Text
from database import Base

class Club(Base):
    __tablename__ = "club"

    id = Column(Integer, primary_key=True)
    uuid = Column(String(40), unique=True, nullable=False, index=True)  # token `sub` / tenant key
    club_name = Column(String(120), nullable=False)
    public_url = Column(String(), default="")
    address = Column(String(255), default="")
    city = Column(String(80), default="")
    country = Column(String(80), default="")
    notes = Column(String, default="")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

class Booking(Base):
    __tablename__ = "booking"
    id = Column(Integer, primary_key=True)
    sync_id = Column(String)
    club_uid = Column(String)
    branch_uid = Column(String)
    code = Column(String)
    lounge_uid = Column(String)
    table_uid = Column(String)
    table_type = Column(String)
    table_number = Column(Integer)
    guest_name = Column(String)
    phone = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String, default="booked")
    customer_id = Column(Integer)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
    deleted_at = Column(DateTime)


class Customer(Base):
    __tablename__ = "customer"
    id = Column(Integer, primary_key=True)
    sync_id = Column(String, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    phone = Column(String, index=True)
    email = Column(String)
    password_hash = Column(String)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Favourite(Base):
    """A customer's starred club (local to this app until central owns it)."""
    __tablename__ = "customer_favourite"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, index=True)
    club_uid = Column(String, index=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Friendship(Base):
    """A directional request that becomes a mutual friendship once accepted.
    requester_id sent it; addressee_id received it. status: pending | accepted."""
    __tablename__ = "friendship"
    id = Column(Integer, primary_key=True)
    requester_id = Column(Integer, index=True)
    addressee_id = Column(Integer, index=True)
    status = Column(String, default="pending")   # pending | accepted
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    __table_args__ = (UniqueConstraint("requester_id", "addressee_id", name="uq_friend_pair"),)


class KhataEntry(Base):
    """A charge a club left on a customer's tab (khata). Lives in central,
    keyed by the central customer id + the club that recorded it. settled_at
    is NULL while it's still owed."""
    __tablename__ = "khata_entry"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, index=True)
    club_uid = Column(String, index=True)
    amount = Column(Integer, default=0)
    description = Column(String, default="")
    source = Column(String, default="")      # 'session' | 'canteen'
    ref = Column(String, default="")         # receipt id / order ref
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    settled_at = Column(DateTime)


class GameLog(Base):
    """A session a customer played at a club — their own copy of the club's
    activity log. Pushed by the club when a bill settles; shown under the
    customer app's Games, with the receipt snapshot rendered by BillingReceipt."""
    __tablename__ = "game_log"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, index=True)
    club_uid = Column(String, index=True)
    club_name = Column(String, default="")
    branch = Column(String, default="")
    lounge = Column(String, default="")
    table_type = Column(String, default="")
    table_number = Column(String, default="")
    minutes = Column(Integer, default=0)
    cost = Column(Integer, default=0)
    payment_status = Column(String, default="")
    payment_method = Column(String, default="")
    receipt_id = Column(String, default="")
    receipt_json = Column(Text, default="")     # full snapshot for BillingReceipt
    played_at = Column(DateTime)
    created_at = Column(DateTime, default=dt.datetime.utcnow)