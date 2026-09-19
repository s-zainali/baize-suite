import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Customer
from schemas import BookingIn
from security import current_customer
from central import central

router = APIRouter(prefix="/customer", tags=["booking"])

@router.get("/table-types")
def table_types(s: Session = Depends(get_db)):
    return central.table_types(s)

@router.get("/availability")
def availability(date: Optional[str] = None, club: Optional[str] = None,
                 branch: Optional[str] = None, s: Session = Depends(get_db)):
    day = dt.date.fromisoformat(date) if date else dt.date.today()
    return central.availability(s, day, club, branch)

@router.post("/bookings")
def create_booking(body: BookingIn, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    start = dt.datetime.fromisoformat(body.startTime); end = dt.datetime.fromisoformat(body.endTime)
    if end <= start:
        raise HTTPException(400, "End time must be after the start.")
    return central.create_booking(s, body.tableUid, start, end, c)

@router.get("/bookings")
def my_bookings(c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    return {"bookings": central.my_bookings(s, c)}

@router.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: int, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    return central.cancel_booking(s, c, booking_id)
