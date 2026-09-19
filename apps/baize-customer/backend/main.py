"""baize-customer API — app assembly. All logic lives in routers/ + central.py."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import config
from routers import auth, clubs, booking

from database import engine, Base
import models  # noqa: F401 (register tables)
Base.metadata.create_all(bind=engine)   # creates customer_favourite if missing (no-op for existing)

app = FastAPI(title="baize-customer")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(clubs.router)
app.include_router(booking.router)

@app.get("/")
def root():
    return {"service": "baize-customer", "ok": True, "mode": "central" if config.CENTRAL_API_URL else "local"}
