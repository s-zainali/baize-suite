"""Central club registry — called by the licence server (service-to-service) to
enlist/delist a club so it shows up (or stops showing up) in the customer app.

Authenticated with a shared admin key (X-Registry-Key) that only the licence
server holds. This is separate from the per-node bridge secret."""
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import config
from database import get_db
from models import Club

router = APIRouter(prefix="/registry", tags=["registry"])


def require_registry_key(x_registry_key: Optional[str] = Header(None)):
    if not config.REGISTRY_ADMIN_KEY:
        raise HTTPException(503, "Registry admin key not configured on the central app.")
    if x_registry_key != config.REGISTRY_ADMIN_KEY:
        raise HTTPException(401, "Unauthorized.")


class ClubIn(BaseModel):
    uuid: str
    clubName: str
    publicUrl: Optional[str] = ""
    city: Optional[str] = ""
    address: Optional[str] = ""
    country: Optional[str] = ""
    notes: Optional[str] = ""


@router.post("/clubs", dependencies=[Depends(require_registry_key)])
def register_club(body: ClubIn, s: Session = Depends(get_db)):
    """Enlist (or update + reactivate) a club. Idempotent by uuid."""
    club = s.query(Club).filter(Club.uuid == body.uuid).first()
    if club is None:
        club = Club(uuid=body.uuid)
        s.add(club)
    club.club_name = body.clubName
    club.public_url = (body.publicUrl or "").strip()
    club.city = body.city or ""
    club.address = body.address or ""
    club.country = body.country or ""
    club.notes = body.notes or ""
    club.is_active = True
    s.commit()
    return {"ok": True, "uuid": club.uuid, "registered": True}


@router.delete("/clubs/{uuid}", dependencies=[Depends(require_registry_key)])
def deregister_club(uuid: str, s: Session = Depends(get_db)):
    """Delist a club — soft (keeps history + any favourites/bookings intact),
    just hidden from discovery. Re-enlisting reactivates it."""
    club = s.query(Club).filter(Club.uuid == uuid).first()
    if not club:
        raise HTTPException(404, "Club not in registry.")
    club.is_active = False
    s.commit()
    return {"ok": True, "uuid": uuid, "registered": False}