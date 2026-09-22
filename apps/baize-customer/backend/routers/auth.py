from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Customer
from schemas import SignUp, SignIn
from security import hash_password, verify_password, make_token, current_customer
import config

router = APIRouter(prefix="/customer", tags=["auth"])

def _out(c): return {"name": c.name, "phone": c.phone, "email": c.email}

@router.post("/register")
def register(body: SignUp, s: Session = Depends(get_db)):
    if s.query(Customer).filter(Customer.phone == body.phone).first():
        raise HTTPException(409, "That phone is already registered.")
    c = Customer(name=body.name, phone=body.phone, email=body.email,
                 password_hash=hash_password(body.password))
    s.add(c); s.commit()
    return {"token": make_token(c), "profile": _out(c)}

@router.post("/login")
def login(body: SignIn, s: Session = Depends(get_db)):
    c = s.query(Customer).filter(Customer.phone == body.phone).first()
    if not c or not verify_password(c.password_hash, body.password):
        raise HTTPException(401, "Wrong phone or password.")
    return {"token": make_token(c), "profile": _out(c)}

@router.get("/me")
def me(c: Customer = Depends(current_customer)):
    return {"profile": _out(c)}
