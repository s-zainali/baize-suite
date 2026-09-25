"""Request/response shapes."""
from typing import Optional, List
from pydantic import BaseModel


class SignUp(BaseModel):
    name: str; phone: str; email: Optional[str] = None; password: str

class SignIn(BaseModel):
    phone: str; password: str

class BookingIn(BaseModel):
    clubUid: str
    branchUid: str
    tableType: str
    tableNumber: str
    loungeUid: str
    tableUid: str
    startTime: str
    endTime: str

class ClubOut(BaseModel):
    uid: str
    logoUrl: Optional[str] = None
    name: str
    city: Optional[str] = None
    branches: int = 0
    favourite: bool = False