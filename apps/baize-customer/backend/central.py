"""
The Baize connection layer — the ONLY place that knows *where* club data comes
from. Routers depend on `Central`, never on the DB or HTTP directly, so moving
from standalone to the central network is a one-line config change.

  • No CENTRAL_API_URL  → LocalCentral  (reads the local shared DB — standalone)
  • CENTRAL_API_URL set → HttpCentral   (calls the baize central API)
"""
from __future__ import annotations
import datetime as dt
import uuid
from abc import ABC, abstractmethod
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
import httpx

import config
from models import Booking, Club


class Central(ABC):
    """Contract for talking to the club network. Every method returns plain
    JSON-able dicts so the two implementations are interchangeable."""

    @abstractmethod
    def list_clubs(self, db: Session, query: Optional[str] = None,
                   near: Optional[str] = None, fav_uids: Optional[set] = None) -> list: ...

    @abstractmethod
    def table_types(self, db: Session) -> list: ...

    @abstractmethod
    def availability(self, db: Session, date: dt.date, club_uid: Optional[str]) -> dict: ...

    @abstractmethod
    def create_booking(self, db: Session, table_uid: str, start: dt.datetime,
                       end: dt.datetime, customer) -> dict: ...

    @abstractmethod
    def my_bookings(self, db: Session, customer) -> list: ...

    @abstractmethod
    def cancel_booking(self, db: Session, customer, booking_id: int) -> dict: ...


class LocalCentral(Central):
    """Standalone: everything comes from the local shared DB."""

    def list_clubs(self, db: Session, query: Optional[str] = None, 
                   near: Optional[str] = None, fav_uids: Optional[set] = None) -> list:
        fav_uids = fav_uids or set()
        
        # Always query all active clubs regardless of config.CLUB_UID
        clubs = db.query(Club).filter(Club.is_active.is_(True)).all()
            
        out = []
        for c in clubs:
            name = c.club_name
            city = c.city or ""
            address = c.address or ""

            # Case-insensitive search filter
            if query:
                q_clean = query.strip().lower()
                target_str = f"{name} {city} {address}".lower()
                if q_clean not in target_str:
                    continue

            # Near / location filter
            if near:
                near_clean = near.strip().lower()
                target_loc = f"{city} {address}".lower()
                if near_clean not in target_loc:
                    continue

            out.append({
                "uid": c.uuid,
                "name": name,
                "city": city,
                "address": address,
                "branches": 1,
                "favourite": c.uuid in fav_uids
            })
            
        return sorted(out, key=lambda x: x["name"].lower())

    def table_types(self, db: Session) -> list:
        return []

    
    def availability(
        self, 
        db: Session, 
        date: dt.date, 
        club_uid: Optional[str], 
        branch_uid: Optional[str] = None
    ) -> dict:
        target_club_uid = club_uid or config.CLUB_UID
        if not target_club_uid:
            raise HTTPException(status_code=400, detail="A valid club_uid is required.")

        club = db.query(Club).filter(Club.uuid == target_club_uid).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found.")

        public_url = getattr(club, "public_url", None)
        if public_url:
            return self._fetch_remote_availability(club.club_name, public_url, date, branch_uid)

        # Standalone / Local DB fallback
        start = dt.datetime.combine(date, dt.time.min)
        end = start + dt.timedelta(days=1)

        busy = db.query(Booking).filter(
            Booking.status.in_(["booked", "active"]),
            Booking.start_time < end,
            Booking.end_time > start,
            Booking.deleted_at.is_(None),
            Booking.club_uid == target_club_uid
        ).all()

        return {
            "club" : club.club_name,
            "date": date.isoformat(),
            "branches": [],
            "selectedBranch": branch_uid,
            "lounges": [],
            "tables": [],
            "busy": [{
                "tableUid": b.table_uid,
                "startTime": b.start_time.isoformat(),
                "endTime": b.end_time.isoformat()
            } for b in busy]
        }

    def _fetch_remote_availability(
        self, 
        club_name: str,
        public_url: str, 
        date: dt.date, 
        branch_uid: Optional[str] = None
    ) -> dict:
        base_url = public_url.rstrip("/")
        url = f"{base_url}/api/customer/availability"
        
        # Build query params dynamically
        params = {"date": date.isoformat()}
        if branch_uid:
            params["branch"] = branch_uid  # Passes ?branch=... to remote node

        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(url, params=params)
                if res.status_code != 200:
                    raise HTTPException(status_code=res.status_code, detail=f"Club node error: {res.text}")
                resJson = res.json()
                resJson['club'] = club_name
                return resJson
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Could not reach club node at {public_url}: {str(e)}"
            )

        
    def create_booking(self, db: Session, table_uid: str, start: dt.datetime, end: dt.datetime, customer) -> dict:
        clash = db.query(Booking).filter(
            Booking.table_uid == table_uid,
            Booking.status.in_(["booked", "active"]),
            Booking.start_time < end,
            Booking.end_time > start,
            Booking.deleted_at.is_(None)
        ).first()

        if clash:
            raise HTTPException(409, "That slot was just taken.")

        b = Booking(
            club_uid=config.CLUB_UID,
            table_uid=table_uid,
            guest_name=customer.name,
            phone=customer.phone,
            start_time=start,
            end_time=end,
            status="booked",
            customer_id=customer.id,
            code=str(uuid.uuid4())[:6].upper()
        )
        db.add(b)
        db.commit()

        return {
            "ok": True,
            "code": b.code,
            "booking": {
                "tableUid": b.table_uid,
                "startTime": start.isoformat(),
                "endTime": end.isoformat()
            }
        }

    def my_bookings(self, db: Session, customer) -> list:
        rows = db.query(Booking).filter(
            Booking.customer_id == customer.id,
            Booking.deleted_at.is_(None)
        ).order_by(Booking.start_time).all()

        return [{
            "id": b.id,
            "code": b.code,
            "tableUid": b.table_uid,
            "tableType": b.table_type,
            "tableNumber": b.table_number,
            "startTime": b.start_time.isoformat(),
            "endTime": b.end_time.isoformat(),
            "status": b.status
        } for b in rows]

    def cancel_booking(self, db: Session, customer, booking_id: int) -> dict:
        b = db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.customer_id == customer.id
        ).first()

        if not b:
            raise HTTPException(404, "No such booking.")

        b.deleted_at = dt.datetime.utcnow()
        b.status = "cancelled"
        db.commit()

        return {"ok": True}


class HttpCentral(Central):
    """Future: the baize central API is the source of truth."""

    def __init__(self, base_url: str, api_key: Optional[str]):
        self.base = base_url.rstrip("/")
        self.key = api_key

    def _headers(self):
        return {"Authorization": f"Bearer {self.key}"} if self.key else {}

    def list_clubs(self, db: Session, query: Optional[str] = None, near: Optional[str] = None, fav_uids: Optional[set] = None) -> list:
        raise NotImplementedError("central: GET /clubs")

    def table_types(self, db: Session) -> list:
        raise NotImplementedError("central: GET /table-types")

    def availability(self, db: Session, date: dt.date, club_uid: Optional[str], branch_uid: Optional[str]) -> dict:
        raise NotImplementedError("central: GET /availability")

    def create_booking(self, db: Session, table_uid: str, start: dt.datetime, end: dt.datetime, customer) -> dict:
        raise NotImplementedError("central: POST /bookings")

    def my_bookings(self, db: Session, customer) -> list:
        raise NotImplementedError("central: GET /bookings")

    def cancel_booking(self, db: Session, customer, booking_id: int) -> dict:
        raise NotImplementedError("central: DELETE /bookings/{id}")


def get_central() -> Central:
    """Chosen once at import by config. Swap standalone↔central via env only."""
    if config.CENTRAL_API_URL:
        return HttpCentral(config.CENTRAL_API_URL, config.CENTRAL_API_KEY)
    return LocalCentral()


central: Central = get_central()