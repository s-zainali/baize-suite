"""SQLAlchemy models — the subset of the shared schema this app reads/writes.
(Matches the club app's tables, including the sync columns.)"""
import uuid
import datetime as dt
from sqlalchemy import Column, Integer, String, DateTime, Boolean
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

class Branch(Base):
    __tablename__ = "branch"
    id = Column(Integer, primary_key=True)
    uid = Column(String); name = Column(String); address = Column(String)
    status = Column(String); club_uid = Column(String); deleted_at = Column(DateTime)


class Lounge(Base):
    __tablename__ = "lounge"
    id = Column(Integer, primary_key=True)
    uid = Column(String); name = Column(String); status = Column(String)
    sort_order = Column(Integer); branch_id = Column(Integer)
    club_uid = Column(String); deleted_at = Column(DateTime)


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


class Favourite(Base):
    """A customer's starred club (local to this app until central owns it)."""
    __tablename__ = "customer_favourite"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, index=True)
    club_uid = Column(String, index=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
