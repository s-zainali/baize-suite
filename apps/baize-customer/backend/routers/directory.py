"""Customer directory for club nodes — the club asks central 'who is this
phone / this id?' when linking a player or starting a booking. Bridge-authed."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Customer
from bridge_verify import require_bridge

router = APIRouter(prefix="/customer/directory", tags=["directory"],
                   dependencies=[Depends(require_bridge)])


def _card(c: Customer) -> dict:
    return {"id": c.id, "name": c.name, "phone": c.phone}


@router.get("/lookup")
def lookup(phone: str = "", s: Session = Depends(get_db)):
    """Exact-match by phone (staff type the full number to link)."""
    phone = (phone or "").strip()
    if not phone:
        return {"found": False}
    c = s.query(Customer).filter(Customer.phone == phone).first()
    return {"found": bool(c), "customer": _card(c) if c else None}


@router.get("/by-id/{customer_id}")
def by_id(customer_id: int, s: Session = Depends(get_db)):
    """Resolve a central customer id (e.g. from a booking) to a name/phone."""
    c = s.get(Customer, customer_id)
    return {"found": bool(c), "customer": _card(c) if c else None}