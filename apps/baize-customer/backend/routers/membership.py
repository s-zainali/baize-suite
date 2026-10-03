"""Memberships — a customer's membership at a club.

A club grants membership (paid, or earned by games) via bridge-authed calls;
the customer views their own memberships. Member perks (khata, discounts) are
enforced by the club, which owns the policy; central just holds the records.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Membership, Customer, Club
from bridge_verify import require_bridge
from security import current_customer

router = APIRouter(prefix="/customer", tags=["membership"])


class GrantIn(BaseModel):
    customerId: int
    clubUid: str
    tier: str = "member"
    source: str = "manual"   # manual (paid) | games (earned)
    note: str = ""


@router.post("/membership", dependencies=[Depends(require_bridge)])
def grant(body: GrantIn, s: Session = Depends(get_db)):
    """Club grants or refreshes a customer's membership (idempotent per pair)."""
    m = (s.query(Membership)
         .filter(Membership.customer_id == body.customerId,
                 Membership.club_uid == body.clubUid).first())
    if m is None:
        m = Membership(customer_id=body.customerId, club_uid=body.clubUid)
        s.add(m)
    m.status = "active"
    m.tier = body.tier or "member"
    m.source = body.source or "manual"
    if body.note:
        m.note = body.note
    s.commit()
    return {"ok": True, "status": m.status, "tier": m.tier}


@router.delete("/membership", dependencies=[Depends(require_bridge)])
def revoke(customerId: int, clubUid: str, s: Session = Depends(get_db)):
    m = (s.query(Membership)
         .filter(Membership.customer_id == customerId,
                 Membership.club_uid == clubUid).first())
    if m:
        m.status = "lapsed"
        s.commit()
    return {"ok": True}


@router.get("/membership/check", dependencies=[Depends(require_bridge)])
def check(customerId: int, clubUid: str, s: Session = Depends(get_db)):
    """Club asks whether a customer is a member (gates khata/discounts)."""
    m = (s.query(Membership)
         .filter(Membership.customer_id == customerId,
                 Membership.club_uid == clubUid,
                 Membership.status == "active").first())
    return {"member": bool(m), "tier": m.tier if m else None}


@router.get("/memberships")
def my_memberships(c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    """The customer's own active memberships, with club names/logos."""
    from cdn import cdn_logo_url
    rows = (s.query(Membership)
            .filter(Membership.customer_id == c.id, Membership.status == "active").all())
    clubs = {cl.uuid: cl for cl in s.query(Club)
             .filter(Club.uuid.in_({m.club_uid for m in rows})).all()}
    out = []
    for m in rows:
        cl = clubs.get(m.club_uid)
        out.append({
            "clubUid": m.club_uid,
            "clubName": cl.club_name if cl else "",
            "logoUrl": cdn_logo_url(m.club_uid),
            "tier": m.tier,
            "source": m.source,
            "since": m.created_at.isoformat() if m.created_at else None,
        })
    return {"memberships": out}