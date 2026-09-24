"""Khata (customer tabs) — lives in central, recorded by clubs against the
central customer id. Bridge-authed (the club calls these)."""
import datetime as dt
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import KhataEntry, Customer
from bridge_verify import require_bridge
from security import current_customer

router = APIRouter(prefix="/customer/khata", tags=["khata"])


class ChargeIn(BaseModel):
    customerId: int
    clubUid: str
    amount: int
    description: str = ""
    source: str = ""
    ref: str = ""

class SettleIn(BaseModel):
    customerId: int
    clubUid: str


@router.post("/charge", dependencies=[Depends(require_bridge)])
def charge(body: ChargeIn, s: Session = Depends(get_db)):
    e = KhataEntry(customer_id=body.customerId, club_uid=body.clubUid, amount=body.amount,
                   description=body.description, source=body.source, ref=body.ref)
    s.add(e); s.commit()
    return {"ok": True, "id": e.id}


@router.get("/book", dependencies=[Depends(require_bridge)])
def book(clubUid: str, s: Session = Depends(get_db)):
    """Open dues for a club, grouped by customer (name resolved from central)."""
    rows = s.query(KhataEntry).filter(KhataEntry.club_uid == clubUid,
                                      KhataEntry.settled_at.is_(None)).all()
    by_cust = {}
    for r in rows:
        g = by_cust.setdefault(r.customer_id, {"customerId": r.customer_id, "total": 0, "entries": []})
        g["total"] += (r.amount or 0)
        g["entries"].append({"id": r.id, "amount": r.amount, "description": r.description,
                             "source": r.source, "ref": r.ref,
                             "createdAt": r.created_at.isoformat() if r.created_at else None})
    for cid, g in by_cust.items():
        c = s.get(Customer, cid)
        g["name"] = c.name if c else f"#{cid}"
        g["phone"] = c.phone if c else ""
    return {"khata": sorted(by_cust.values(), key=lambda x: -x["total"])}


@router.post("/settle", dependencies=[Depends(require_bridge)])
def settle(body: SettleIn, s: Session = Depends(get_db)):
    n = (s.query(KhataEntry)
         .filter(KhataEntry.customer_id == body.customerId,
                 KhataEntry.club_uid == body.clubUid,
                 KhataEntry.settled_at.is_(None))
         .update({"settled_at": dt.datetime.utcnow()}))
    s.commit()
    return {"ok": True, "settled": n}


@router.get("")
def my_khata(c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    """The customer's own outstanding tab across every club they owe."""
    from models import Club
    rows = (s.query(KhataEntry)
            .filter(KhataEntry.customer_id == c.id, KhataEntry.settled_at.is_(None))
            .order_by(KhataEntry.created_at).all())
    club_names = {cl.uuid: cl.club_name for cl in s.query(Club)
                  .filter(Club.uuid.in_({r.club_uid for r in rows if r.club_uid})).all()}
    bills = [{
        "id": r.id,
        "kind": r.source or "session",
        "ref": r.ref or "",
        "amount": r.amount or 0,
        "description": r.description or "",
        "clubUid": r.club_uid,
        "clubName": club_names.get(r.club_uid, ""),
    } for r in rows]
    return {
        "outstanding": sum(b["amount"] for b in bills),
        "bills": bills,
        "payUrl": None,   # aggregator QR is wired per-club at settle time
    }