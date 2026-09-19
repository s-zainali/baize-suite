from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Customer, Favourite
from security import current_customer
from central import central

router = APIRouter(prefix="/customer", tags=["clubs"])

def _fav_uids(s, customer_id):
    return {f.club_uid for f in s.query(Favourite).filter(Favourite.customer_id == customer_id).all()}

@router.get("/clubs")
def list_clubs(q: Optional[str] = None, near: Optional[str] = None,
               s: Session = Depends(get_db)):
    """Public discovery: search + (later) near-you. Favourites are marked per
    customer only when signed in — see /clubs/favourites."""
    return {"clubs": central.list_clubs(s, query=q, near=near)}

@router.get("/clubs/favourites")
def favourites(c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    fav = _fav_uids(s, c.id)
    clubs = [club for club in central.list_clubs(s, fav_uids=fav) if club["uid"] in fav]
    return {"clubs": clubs}

@router.post("/clubs/{club_uid}/favourite")
def add_favourite(club_uid: str, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    if not s.query(Favourite).filter(Favourite.customer_id == c.id, Favourite.club_uid == club_uid).first():
        s.add(Favourite(customer_id=c.id, club_uid=club_uid)); s.commit()
    return {"ok": True, "favourite": True}

@router.delete("/clubs/{club_uid}/favourite")
def remove_favourite(club_uid: str, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    s.query(Favourite).filter(Favourite.customer_id == c.id, Favourite.club_uid == club_uid).delete()
    s.commit()
    return {"ok": True, "favourite": False}
