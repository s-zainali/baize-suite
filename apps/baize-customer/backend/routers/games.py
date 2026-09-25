"""A customer's game history — their own record of sessions across clubs.
Clubs push here on settle (bridge-authed); the customer reads their own (JWT)."""
import datetime as dt
import json
from cdn import cdn_logo_url
from collections import Counter
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import GameLog, Customer, Club
from security import current_customer
from bridge_verify import require_bridge

router = APIRouter(prefix="/customer/games", tags=["games"])


def _parse(v):
    try:
        return dt.datetime.fromisoformat(v) if v else None
    except (ValueError, TypeError):
        return None


class GameIn(BaseModel):
    customerId: int
    clubUid: str = ""
    clubName: str = ""
    branch: str = ""
    lounge: str = ""
    tableType: str = ""
    tableNumber: str = ""
    minutes: int = 0
    cost: int = 0
    paymentStatus: str = ""
    paymentMethod: str = ""
    receiptId: str = ""
    receipt: dict = {}
    playedAt: Optional[str] = None


@router.post("", dependencies=[Depends(require_bridge)])
def record(body: GameIn, s: Session = Depends(get_db)):
    """Idempotent by (customer, club, receiptId) so a resent settle can't
    double-log the same game."""
    if body.receiptId:
        existing = s.query(GameLog).filter(GameLog.customer_id == body.customerId,
                                           GameLog.club_uid == body.clubUid,
                                           GameLog.receipt_id == str(body.receiptId)).first()
        if existing:
            existing.payment_status = body.paymentStatus
            existing.payment_method = body.paymentMethod
            existing.cost = body.cost
            existing.receipt_json = json.dumps(body.receipt or {})
            s.commit()
            return {"ok": True, "id": existing.id, "updated": True}
        club_name = s.query(Club.club_name).filter(Club.uuid == body.clubUid).scalar()
    g = GameLog(customer_id=body.customerId, club_uid=body.clubUid, club_name=club_name,
                branch=body.branch, lounge=body.lounge, table_type=body.tableType,
                table_number=str(body.tableNumber), minutes=body.minutes, cost=body.cost,
                payment_status=body.paymentStatus, payment_method=body.paymentMethod,
                receipt_id=str(body.receiptId), receipt_json=json.dumps(body.receipt or {}),
                played_at=_parse(body.playedAt) or dt.datetime.utcnow())
    s.add(g); s.commit()
    return {"ok": True, "id": g.id}


@router.get("")
def my_games(limit: int = 50, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    rows = (s.query(GameLog).filter(GameLog.customer_id == c.id)
            .order_by(GameLog.played_at.desc(), GameLog.id.desc()).limit(limit).all())
    # resolve each club's logo (path is in the receipt snapshot; base is the node URL)
    clubs = {cl.uuid: cl for cl in s.query(Club)
             .filter(Club.uuid.in_({g.club_uid for g in rows if g.club_uid})).all()}

    def _logo(g):
        return cdn_logo_url(g.club_uid)

    games = [{"id": g.id, "clubName": g.club_name, "branch": g.branch, "lounge": g.lounge,
              "clubLogo": _logo(g),
              "tableType": g.table_type, "tableNumber": g.table_number, "minutes": g.minutes,
              "cost": g.cost, "receiptId": g.receipt_id, "paymentStatus": g.payment_status,
              "playedAt": g.played_at.isoformat() if g.played_at else None} for g in rows]
    minutes = sum(g["minutes"] or 0 for g in games)
    fav = Counter(g["tableType"] for g in games if g["tableType"]).most_common(1)
    top = Counter(g["clubName"] for g in games if g["clubName"]).most_common(1)
    return {"games": games,
            "summary": {
                "gamesPlayed": len(games),
                "minutesPlayed": minutes,
                "favourite": {"type": fav[0][0], "plays": fav[0][1]} if fav else None,
                "topClub": {"name": top[0][0], "plays": top[0][1]} if top else None,
            }}


@router.get("/{game_id}/receipt")
def game_receipt(game_id: int, c: Customer = Depends(current_customer), s: Session = Depends(get_db)):
    g = s.query(GameLog).filter(GameLog.id == game_id, GameLog.customer_id == c.id).first()
    if not g:
        raise HTTPException(404, "No such game.")
    receipt = json.loads(g.receipt_json or "{}")
    # The club logo lives on the club's own server — tell the receipt where to
    # load it from, and backfill name/address from the registry if needed.
    club = s.query(Club).filter(Club.uuid == g.club_uid).first() if g.club_uid else None
    b = receipt.setdefault("branding", {})
    if club:
        b.setdefault("clubName", club.club_name)
        b.setdefault("address", club.address or "")
    b["logoUrl"] = cdn_logo_url(g.club_uid)          # deterministic CDN URL
    receipt["logoBase"] = ""                          # logoUrl is absolute
    return receipt