"""Central club registry — called by the licence server (service-to-service) to
enlist/delist a club so it shows up (or stops showing up) in the customer app.

Authenticated with a shared admin key (X-Registry-Key) that only the licence
server holds. This is separate from the per-node bridge secret."""
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import hmac
import ipaddress
from urllib.parse import urlparse

import config
from database import get_db
from models import Club

router = APIRouter(prefix="/registry", tags=["registry"])


def _validate_public_url(url: str):
    """Reject non-https or internal/loopback targets — this URL is fetched
    server-side by the customer app, so it must point at a public node."""
    if not url:
        return
    u = urlparse(url)
    if not config.IS_PROD:
        return   # dev/local installs may use http://localhost:PORT etc.
    if u.scheme != "https":
        raise HTTPException(400, "public_url must be https.")
    host = u.hostname or ""
    if host == "localhost" or host.endswith(".local"):
        raise HTTPException(400, "public_url must be a public host.")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise HTTPException(400, "public_url must be a public host.")
    except ValueError:
        pass  # a hostname, not a literal IP


def require_registry_key(x_registry_key: Optional[str] = Header(None)):
    if not config.REGISTRY_ADMIN_KEY:
        raise HTTPException(503, "Registry admin key not configured on the central app.")
    if not hmac.compare_digest(x_registry_key or "", config.REGISTRY_ADMIN_KEY):
        raise HTTPException(401, "Unauthorized.")


class ClubIn(BaseModel):
    uuid: str
    clubName: str
    publicUrl: Optional[str] = ""
    city: Optional[str] = ""
    address: Optional[str] = ""
    country: Optional[str] = ""
    branches: Optional[int] = 1
    notes: Optional[str] = ""


@router.post("/clubs", dependencies=[Depends(require_registry_key)])
def register_club(body: ClubIn, s: Session = Depends(get_db)):
    """Enlist (or update + reactivate) a club. Idempotent by uuid."""
    club = s.query(Club).filter(Club.uuid == body.uuid).first()
    if club is None:
        club = Club(uuid=body.uuid)
        s.add(club)
    club.club_name = body.clubName
    _validate_public_url((body.publicUrl or "").strip())
    club.public_url = (body.publicUrl or "").strip()
    club.branches = max(1, int(body.branches or 1))
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