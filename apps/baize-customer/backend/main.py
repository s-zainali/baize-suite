"""baize-customer API — app assembly. All logic lives in routers/ + central.py."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import config
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import auth, clubs, booking, registry, friends

from database import engine, Base
import models  # noqa: F401 (register tables)
Base.metadata.create_all(bind=engine)   # creates customer_favourite if missing (no-op for existing)

app = FastAPI(title="baize-customer")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router, prefix="/api")
app.include_router(clubs.router, prefix="/api")
app.include_router(booking.router, prefix="/api")
app.include_router(registry.router, prefix="/api")
app.include_router(friends.router, prefix="/api")

DIST_DIR = "../dist"

if os.path.exists(DIST_DIR):

    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="frontend")

    @app.get("/{catchall:path}")
    def serve_frontend(catchall: str):
        # Prevent swallowing broken API endpoint errors
        if catchall.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
            
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {"service": "baize-customer (API mode only)", "ok": True}