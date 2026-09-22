"""Friends — search players, send/accept/decline requests, list friends,
remove, and suggested players (friends-of-friends by mutual count)."""
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from database import get_db
from models import Customer, Friendship
from security import current_customer

router = APIRouter(prefix="/customer", tags=["friends"])


def _card(c: Customer) -> dict:
    return {"id": c.id, "name": c.name, "phone": c.phone, "isOnline": False}


def _accepted_ids(s: Session, me_id: int) -> set:
    rows = s.query(Friendship).filter(
        Friendship.status == "accepted",
        or_(Friendship.requester_id == me_id, Friendship.addressee_id == me_id)).all()
    return {r.addressee_id if r.requester_id == me_id else r.requester_id for r in rows}


@router.get("/friends")
def list_friends(c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    ids = _accepted_ids(s, c.id)
    friends = s.query(Customer).filter(Customer.id.in_(ids)).all() if ids else []
    return {"friends": [_card(f) for f in friends]}


@router.get("/friends/requests")
def incoming_requests(c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    rows = s.query(Friendship).filter(Friendship.addressee_id == c.id,
                                      Friendship.status == "pending").all()
    out = []
    for r in rows:
        u = s.get(Customer, r.requester_id)
        if u:
            out.append({"requestId": r.id, "from": _card(u)})
    return {"requests": out}


@router.get("/friends/suggested")
def suggested(c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    mine = _accepted_ids(s, c.id)
    if not mine:
        return {"suggested": []}
    mutual = Counter()
    for fid in mine:
        for other in _accepted_ids(s, fid):
            if other != c.id and other not in mine:
                mutual[other] += 1
    top = [uid for uid, _ in mutual.most_common(6)]
    if not top:
        return {"suggested": []}
    users = {u.id: u for u in s.query(Customer).filter(Customer.id.in_(top)).all()}
    return {"suggested": [{**_card(users[uid]), "mutuals": mutual[uid]} for uid in top if uid in users]}


@router.get("/friends/search")
def search(q: str = "", c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    q = (q or "").strip()
    if len(q) < 2:
        return {"results": []}
    matches = s.query(Customer).filter(
        Customer.id != c.id,
        or_(Customer.name.ilike(f"%{q}%"), Customer.phone.ilike(f"%{q}%"))).limit(20).all()
    accepted = _accepted_ids(s, c.id)
    pend = s.query(Friendship).filter(
        Friendship.status == "pending",
        or_(Friendship.requester_id == c.id, Friendship.addressee_id == c.id)).all()
    out_ids = {r.addressee_id for r in pend if r.requester_id == c.id}
    in_ids = {r.requester_id for r in pend if r.addressee_id == c.id}

    def rel(uid):
        if uid in accepted: return "friend"
        if uid in out_ids:  return "pending_out"
        if uid in in_ids:   return "pending_in"
        return "none"
    return {"results": [{**_card(m), "status": rel(m.id)} for m in matches]}


class RequestIn(BaseModel):
    customerId: int

@router.post("/friends/requests")
def send_request(body: RequestIn, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    if body.customerId == c.id:
        raise HTTPException(400, "You can't add yourself.")
    if not s.get(Customer, body.customerId):
        raise HTTPException(404, "No such player.")
    if body.customerId in _accepted_ids(s, c.id):
        return {"ok": True, "status": "friend"}
    # they already asked me → accept it (mutual)
    theirs = s.query(Friendship).filter(
        Friendship.requester_id == body.customerId, Friendship.addressee_id == c.id,
        Friendship.status == "pending").first()
    if theirs:
        theirs.status = "accepted"; s.commit()
        return {"ok": True, "status": "friend"}
    mine = s.query(Friendship).filter(
        Friendship.requester_id == c.id, Friendship.addressee_id == body.customerId).first()
    if mine:
        return {"ok": True, "status": "pending_out"}
    s.add(Friendship(requester_id=c.id, addressee_id=body.customerId, status="pending")); s.commit()
    return {"ok": True, "status": "pending_out"}


@router.post("/friends/requests/{request_id}/accept")
def accept(request_id: int, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    r = s.query(Friendship).filter(Friendship.id == request_id,
                                   Friendship.addressee_id == c.id,
                                   Friendship.status == "pending").first()
    if not r:
        raise HTTPException(404, "No such request.")
    r.status = "accepted"; s.commit()
    return {"ok": True}


@router.post("/friends/requests/{request_id}/decline")
def decline(request_id: int, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    r = s.query(Friendship).filter(Friendship.id == request_id,
                                   Friendship.addressee_id == c.id).first()
    if not r:
        raise HTTPException(404, "No such request.")
    s.delete(r); s.commit()
    return {"ok": True}


@router.delete("/friends/{customer_id}")
def remove_friend(customer_id: int, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    rows = s.query(Friendship).filter(Friendship.status == "accepted", or_(
        and_(Friendship.requester_id == c.id, Friendship.addressee_id == customer_id),
        and_(Friendship.requester_id == customer_id, Friendship.addressee_id == c.id))).all()
    for r in rows:
        s.delete(r)
    s.commit()
    return {"ok": True}