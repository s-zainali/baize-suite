"""Request/response shapes."""
from typing import Optional, List
from pydantic import BaseModel


class SignUp(BaseModel):
    name: str; phone: str; email: Optional[str] = None; password: str

class SignIn(BaseModel):
    phone: str; password: str

class BookingIn(BaseModel):
    tableUid: str
    startTime: str
    endTime: str

class ClubOut(BaseModel):
    uid: str
    name: str
    city: Optional[str] = None
    branches: int = 0
    favourite: bool = False
