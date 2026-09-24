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
import config
from abc import ABC, abstractmethod
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
import json
import httpx

import config
import bridge
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
    def create_booking(self, db: Session, club_uid: str, branch_uid: str, table_type: str, table_number: str, lounge_uid: str, table_uid:str, start: dt.datetime,
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
                "branches": getattr(c, "branches", 1) or 1,
                "favourite": c.uuid in fav_uids,
                "logoUrl": f"{c.public_url.rstrip('/')}/api/branding/logo" if c.public_url else None,
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

        headers = bridge.sign("GET", "/api/customer/availability")
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(url, params=params, headers=headers)
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

        
    def create_booking(
        self, 
        db: Session, 
        club_uid: str, 
        branch_uid: str, 
        table_type: str, 
        table_number: str, 
        lounge_uid: str, 
        table_uid: str, 
        start: dt.datetime, 
        end: dt.datetime, 
        customer
    ) -> dict:
        # 0. Idempotency — a retried / double-submitted booking for the same slot
        # by the same customer returns the existing one instead of duplicating.
        dup = db.query(Booking).filter(
            Booking.customer_id == customer.id,
            Booking.table_uid == table_uid,
            Booking.start_time == start,
            Booking.status.in_(["booked", "active"]),
            Booking.deleted_at.is_(None),
        ).first()
        if dup:
            return {"success": True, "code": dup.code, "syncId": dup.sync_id, "duplicate": True}

        # 1. Local conflict check (someone else on the same slot)
        clash = db.query(Booking).filter(
            Booking.table_uid == table_uid,
            Booking.status.in_(["booked", "active"]),
            Booking.start_time < end,
            Booking.end_time > start,
            Booking.deleted_at.is_(None)
        ).first()

        if clash:
            raise HTTPException(status_code=409, detail="That slot was just taken.")

        # 2. Fetch club/branch node details to get destination base URL
        club = db.query(Club).filter(Club.uuid == club_uid).first()
        if not club or not getattr(club, "public_url", None):
            raise HTTPException(status_code=400, detail="Target node URL not configured.")

        booking_code = str(uuid.uuid4())[:6].upper()

        # 3. Save to local DB first
        sync_id = str(uuid.uuid4())
        b = Booking(
            sync_id = sync_id,
            club_uid=club_uid,
            branch_uid=branch_uid,
            table_type=table_type,
            table_number=table_number,
            lounge_uid=lounge_uid,
            table_uid=table_uid,
            guest_name=customer.name,
            phone=customer.phone,
            start_time=start,
            end_time=end,
            status="booked",
            customer_id=customer.id,
            code=booking_code
        )
        
        try:
            db.add(b)
            db.commit()
            db.refresh(b)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create local booking: {str(e)}")

        # 4. Local save was successful — forward to the target node endpoint
        target_url = f"{club.public_url.rstrip('/')}/api/customer/bookings"
        payload = {
            "syncId": sync_id,
            "tableUid": table_uid,
            "startTime": start.isoformat(),
            "endTime": end.isoformat(),
            "guestName": customer.name,
            "phone": customer.phone,
            "customerId": customer.id,
            "bookingCode" : booking_code
        }

        body = json.dumps(payload).encode()
        headers = {**bridge.sign("POST", "/api/customer/bookings", body),
                   "Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(target_url, content=body, headers=headers)

                if res.status_code not in (200, 201):
                    # Node rejected the booking; rollback local booking to keep state synchronized
                    db.delete(b)
                    db.commit()

                    err_msg = res.json().get("error", res.text) if "application/json" in (res.headers.get("content-type") or "") else res.text
                    raise HTTPException(
                        status_code=res.status_code, 
                        detail=f"Local booking cancelled because remote node rejected request: {err_msg}"
                    )

        except httpx.RequestError:
            # Node unreachable OR its response was lost. DO NOT delete: the node
            # may have created the booking (its create is idempotent by syncId),
            # and deleting here would make a retry mint a NEW syncId → a duplicate
            # at the club. Keep the booking; it reconciles on the next sync/retry.
            db.commit()
            return {"success": True, "code": booking_code, "syncId": sync_id, "pendingSync": True}

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
            Booking.status.in_(['booked', 'active']),   # upcoming + in-progress
            Booking.deleted_at.is_(None)
        ).order_by(Booking.start_time).all()

        seen, out = set(), []
        for b in rows:
            if b.sync_id in seen:        # never show one booking twice
                continue
            seen.add(b.sync_id)
            out.append({
                "id": b.id,
                "code": b.code,
                "tableUid": b.table_uid,
                "tableType": b.table_type,
                "tableNumber": b.table_number,
                "startTime": b.start_time.isoformat(),
                "endTime": b.end_time.isoformat(),
                "status": b.status,        # 'booked' = upcoming, 'active' = playing now
            })
        return out

    def cancel_booking(self, db: Session, customer, booking_id: int) -> dict:
        b = db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.customer_id == customer.id
        ).first()


        if not b:
            raise HTTPException(404, "No such booking.")
        club_uid = b.club_uid
        club = db.query(Club).filter(Club.uuid == club_uid).first()
        if not club or not getattr(club, "public_url", None):
            raise HTTPException(status_code=400, detail="Target node URL not configured.")
        target_url = f"{club.public_url.rstrip('/')}/api/customer/bookings/{b.sync_id}"
        headers = bridge.sign("DELETE", f"/api/customer/bookings/{b.sync_id}")
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.delete(target_url, headers=headers)

                if res.status_code not in (200, 201):
                    # Node rejected the booking; rollback local booking to keep state synchronized

                    err_msg = res.json().get("error", res.text) if "application/json" in (res.headers.get("content-type") or "") else res.text
                    raise HTTPException(
                        status_code=res.status_code, 
                        detail=f"Local booking not cancelled because remote node rejected request: {err_msg}"
                    )

        except httpx.RequestError as e:
            # Node was unreachable; delete local booking to prevent orphaned state
            raise HTTPException(
                status_code=502, 
                detail=f"Local booking not cancelled because remote node was unreachable: {str(e)}"
            )
        try:
            b.deleted_at = dt.datetime.utcnow()
            b.status = "cancelled"
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete local booking: {str(e)}")

        return {"ok": True}
    
    def cancel_booking_sync(self, db: Session, sync_id: str) -> dict:
        b = db.query(Booking).filter(
            Booking.sync_id == sync_id,
        ).first()


        if not b:
            raise HTTPException(404, "No such booking.")
        
        try:
            b.deleted_at = dt.datetime.utcnow()
            b.status = "cancelled"
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete local booking: {str(e)}")

        return {"ok": True}
    
    def mark_booking_sync(self, db: Session, sync_id: str, status: str) -> dict:
        b = db.query(Booking).filter(
            Booking.sync_id == sync_id,
        ).first()

        if not b:
            raise HTTPException(404, "No such booking.")
        
        try:
            b.status = status
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to complete local booking: {str(e)}")

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
    """LocalCentral IS the network layer now: it reads the club registry from
    this app's DB and fans out to each club node over the signed bridge. The
    old HttpCentral (single upstream API) is kept only as a stub and is never
    selected — routing per-club by public_url replaced it."""
    return LocalCentral()


central: Central = get_central()