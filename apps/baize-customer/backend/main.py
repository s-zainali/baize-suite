"""baize-customer API — app assembly. All logic lives in routers/ + central.py."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import config
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import auth, clubs, booking

from database import engine, Base
import models  # noqa: F401 (register tables)
Base.metadata.create_all(bind=engine)   # creates customer_favourite if missing (no-op for existing)

app = FastAPI(title="baize-customer")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router, prefix="/api")
app.include_router(clubs.router, prefix="/api")
app.include_router(booking.router, prefix="/api")

DIST_DIR = "../dist"

if os.path.exists(DIST_DIR):
    # Mount internal compiled assets (js, css, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="static")

    # Catch-all route to serve index.html for Vue client-side page routing
    @app.get("/{catchall:path}")
    def serve_frontend(catchall: str):
        # Prevent the single-page app fallback from swallowing api calls if someone hits a bad endpoint
        if catchall.startswith("customer/"):
            return FileResponse(os.path.join(DIST_DIR, "index.html"))
            
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
else:
    # Fallback endpoint if running locally without a compiled build
    @app.get("/")
    def root():
        return {"service": "baize-customer (API mode only)", "ok": True}