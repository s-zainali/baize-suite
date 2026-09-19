"""Clubs router — handles club discovery, availability, and user favorites."""
import datetime as dt
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Header, HTTPException
from sqlalchemy.orm import Session

import jwt
from config import JWT_SECRET
from database import get_db
from models import Favourite, Customer
from security import current_customer
from schemas import ClubOut
from central import central

router = APIRouter(prefix="/customer/clubs", tags=["clubs"])


def optional_customer(authorization: str = Header(None), db: Session = Depends(get_db)) -> Optional[Customer]:
    """Retrieves customer if token is provided, otherwise returns None (for guest searching)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        claims = jwt.decode(authorization[7:], JWT_SECRET, algorithms=["HS256"])
        return db.get(Customer, int(claims.get("sub", 0)))
    except jwt.InvalidTokenError:
        return None


@router.get("", response_model=List[ClubOut])
def list_clubs(
    query: Optional[str] = Query(None, alias="query"),
    near: Optional[str] = Query(None, alias="near"),
    db: Session = Depends(get_db),
    customer: Optional[Customer] = Depends(optional_customer)
):
    """List or search clubs matching search or proximity filters."""
    fav_uids = set()
    if customer:
        fav_uids = {
            f.club_uid for f in db.query(Favourite).filter(Favourite.customer_id == customer.id).all()
        }
    return central.list_clubs(db=db, query=query, near=near, fav_uids=fav_uids)


@router.post("/{club_uid}/favourite")
def favourite_club(
    club_uid: str,
    db: Session = Depends(get_db),
    customer: Customer = Depends(current_customer)
):
    """Mark a club as favorited for the authenticated customer."""
    existing = db.query(Favourite).filter(
        Favourite.customer_id == customer.id,
        Favourite.club_uid == club_uid
    ).first()
    if not existing:
        fav = Favourite(customer_id=customer.id, club_uid=club_uid)
        db.add(fav)
        db.commit()
    return {"ok": True, "favourite": True}


@router.delete("/{club_uid}/favourite")
def unfavourite_club(
    club_uid: str,
    db: Session = Depends(get_db),
    customer: Customer = Depends(current_customer)
):
    """Unfavorite a club for the authenticated customer."""
    existing = db.query(Favourite).filter(
        Favourite.customer_id == customer.id,
        Favourite.club_uid == club_uid
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
    return {"ok": True, "favourite": False}


@router.get("/table-types")
def get_table_types(db: Session = Depends(get_db)):
    """Get active table types and UI rendering configs."""
    return central.table_types(db)


@router.get("/{club_uid}/availability")
def get_availability(
    club_uid: str,
    date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Fetch lounge, table layout, rates, and active reservations for a given date."""
    try:
        parsed_date = dt.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
    return central.availability(db=db, date=parsed_date, club_uid=club_uid)