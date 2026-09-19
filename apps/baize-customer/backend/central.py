"""
The Baize connection layer — the ONLY place that knows *where* club data comes
from. Routers depend on `Central`, never on the DB or HTTP directly, so moving
from standalone to the central network is a one-line config change.

  • No CENTRAL_API_URL  → LocalCentral  (reads the local shared DB — standalone)
  • CENTRAL_API_URL set → HttpCentral   (calls the baize central API)

To go live on central: fill in HttpCentral's request bodies (each method already
names its endpoint) and set CENTRAL_API_URL. Nothing else changes.
"""
from __future__ import annotations
import datetime as dt
from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

import config
from models import Branch, Lounge, PoolTable, GlobalRate, Booking, TableType


class Central(ABC):
    """Contract for talking to the club network. Every method returns plain
    JSON-able dicts so the two implementations are interchangeable."""

    @abstractmethod
    def list_clubs(self, db: Session, query: Optional[str] = None,
                   near: Optional[str] = None, fav_uids: Optional[set] = None) -> list: ...

    @abstractmethod
    def table_types(self, db: Session) -> list: ...

    @abstractmethod
    def availability(self, db: Session, date: dt.date, club_uid: Optional[str],
                     branch_uid: Optional[str]) -> dict: ...

    @abstractmethod
    def create_booking(self, db: Session, table_uid: str, start: dt.datetime,
                       end: dt.datetime, customer) -> dict: ...

    @abstractmethod
    def my_bookings(self, db: Session, customer) -> list: ...

    @abstractmethod
    def cancel_booking(self, db: Session, customer, booking_id: int) -> dict: ...


class LocalCentral(Central):
    """Standalone: everything comes from the local shared DB."""

    def _clubs_query(self, db):
        q = db.query(Branch).filter(Branch.deleted_at.is_(None))
        return q.filter(Branch.club_uid == config.CLUB_UID) if config.CLUB_UID else q

    def list_clubs(self, db, query=None, near=None, fav_uids=None):
        fav_uids = fav_uids or set()
        by_club: dict[str, list[Branch]] = {}
        for b in self._clubs_query(db).all():
            by_club.setdefault(b.club_uid, []).append(b)
        out = []
        for club_uid, branches in by_club.items():
            if not club_uid:
                continue
            # derive a display name from the branches' common prefix ("Z Snooker - Branch 1")
            name = (branches[0].name or "Club").split(" - ")[0].strip() or f"Club {club_uid[:6]}"
            city = next((b.address.split(",")[-1].strip() for b in branches if b.address), None)
            if query and query.lower() not in f"{name} {city or ''}".lower():
                continue
            out.append({"uid": club_uid, "name": name, "city": city,
                        "branches": len(branches), "favourite": club_uid in fav_uids})
        # near-you needs coordinates (central will supply them); locally just sort by name.
        return sorted(out, key=lambda c: c["name"].lower())

    def table_types(self, db):
        return [{"key": t.key, "id": t.key, "value": t.key, "label": t.label, "color": t.color,
                 "renderer": t.renderer, "badge": t.badge, "sortOrder": t.sort_order}
                for t in db.query(TableType).order_by(TableType.sort_order).all()]

    def availability(self, db, date, club_uid, branch_uid):
        start = dt.datetime.combine(date, dt.time.min); end = start + dt.timedelta(days=1)
        weekend = date.weekday() >= 5
        bq = db.query(Branch).filter(Branch.deleted_at.is_(None))
        if club_uid:  bq = bq.filter(Branch.club_uid == club_uid)
        elif config.CLUB_UID: bq = bq.filter(Branch.club_uid == config.CLUB_UID)
        branches = bq.order_by(Branch.id).all()
        chosen = next((b for b in branches if b.uid == branch_uid), None) \
            or (branches[0] if len(branches) == 1 else None)
        base = {"date": date.isoformat(),
                "branches": [{"uid": b.uid, "name": b.name} for b in branches],
                "selectedBranch": chosen.uid if chosen else None,
                "lounges": [], "tables": [], "busy": []}
        if not chosen:
            return base
        lounges = db.query(Lounge).filter(Lounge.status != "deleted", Lounge.branch_id == chosen.id).all()
        tables = db.query(PoolTable).filter(PoolTable.status != "deleted", PoolTable.branch_id == chosen.id)\
            .order_by(PoolTable.sort_order).all()
        rates = {r.table_type: r for r in db.query(GlobalRate).filter(
            or_(GlobalRate.branch_id == chosen.id, GlobalRate.branch_id.is_(None))).all()}
        busy = db.query(Booking).filter(Booking.branch_id == chosen.id,
                                        Booking.status.in_(["booked", "active"]),
                                        Booking.start_time < end, Booking.end_time > start,
                                        Booking.deleted_at.is_(None)).all()
        def rate(tt):
            r = rates.get(tt); return (r.weekend_rate if weekend else r.weekday_rate) if r else 0
        base.update({
            "lounges": [{"uid": lo.uid, "name": lo.name} for lo in lounges],
            "tables": [{"uid": t.uid, "id": t.table_id, "type": t.table_type, "loungeUid": t.lounge_uid,
                        "isActive": bool(t.is_active), "currentRate": rate(t.table_type)} for t in tables],
            "busy": [{"tableUid": b.table_uid, "startTime": b.start_time.isoformat(),
                      "endTime": b.end_time.isoformat()} for b in busy],
        })
        return base

    def create_booking(self, db, table_uid, start, end, customer):
        import uuid
        from fastapi import HTTPException
        table = db.query(PoolTable).filter(PoolTable.uid == table_uid, PoolTable.status != "deleted").first()
        if not table:
            raise HTTPException(404, "That table doesn't exist.")
        clash = db.query(Booking).filter(Booking.table_uid == table.uid,
                                         Booking.status.in_(["booked", "active"]),
                                         Booking.start_time < end, Booking.end_time > start,
                                         Booking.deleted_at.is_(None)).first()
        if clash:
            raise HTTPException(409, "That slot was just taken.")
        b = Booking(branch_id=table.branch_id, club_uid=table.club_uid, table_uid=table.uid,
                    table_type=table.table_type, guest_name=customer.name, phone=customer.phone,
                    start_time=start, end_time=end, status="booked", customer_id=customer.id,
                    code=str(uuid.uuid4())[:6].upper())
        db.add(b); db.commit()
        return {"ok": True, "code": b.code,
                "booking": {"tableUid": b.table_uid, "startTime": start.isoformat(), "endTime": end.isoformat()}}

    def my_bookings(self, db, customer):
        rows = db.query(Booking).filter(Booking.customer_id == customer.id,
                                        Booking.deleted_at.is_(None)).order_by(Booking.start_time).all()
        return [{"id": b.id, "code": b.code, "tableUid": b.table_uid, "tableType": b.table_type,
                 "tableNumber": b.table_number, "startTime": b.start_time.isoformat(),
                 "endTime": b.end_time.isoformat(), "status": b.status} for b in rows]

    def cancel_booking(self, db, customer, booking_id):
        import datetime as _dt
        from fastapi import HTTPException
        b = db.query(Booking).filter(Booking.id == booking_id, Booking.customer_id == customer.id).first()
        if not b:
            raise HTTPException(404, "No such booking.")
        b.deleted_at = _dt.datetime.utcnow(); b.status = "cancelled"; db.commit()
        return {"ok": True}


class HttpCentral(Central):
    """Future: the baize central API is the source of truth. Each method maps to
    a central endpoint — fill in the request/response mapping when central ships.
    The DB session is ignored here (central owns the data)."""

    def __init__(self, base_url: str, api_key: Optional[str]):
        self.base = base_url.rstrip("/")
        self.key = api_key

    def _headers(self):
        return {"Authorization": f"Bearer {self.key}"} if self.key else {}

    def list_clubs(self, db, query=None, near=None, fav_uids=None):
        # GET {base}/clubs?q=<query>&near=<lat,lng>   → [{uid,name,city,branches}]
        raise NotImplementedError("central: GET /clubs")

    def table_types(self, db):
        # GET {base}/clubs/{club}/table-types
        raise NotImplementedError("central: GET /table-types")

    def availability(self, db, date, club_uid, branch_uid):
        # GET {base}/clubs/{club}/branches/{branch}/availability?date=
        raise NotImplementedError("central: GET /availability")

    def create_booking(self, db, table_uid, start, end, customer):
        # POST {base}/bookings  { tableUid, startTime, endTime, customer }
        raise NotImplementedError("central: POST /bookings")

    def my_bookings(self, db, customer):
        # GET {base}/customers/{id}/bookings
        raise NotImplementedError("central: GET /bookings")

    def cancel_booking(self, db, customer, booking_id):
        # DELETE {base}/bookings/{id}
        raise NotImplementedError("central: DELETE /bookings/{id}")


def get_central() -> Central:
    """Chosen once at import by config. Swap standalone↔central via env only."""
    if config.CENTRAL_API_URL:
        return HttpCentral(config.CENTRAL_API_URL, config.CENTRAL_API_KEY)
    return LocalCentral()


central: Central = get_central()
