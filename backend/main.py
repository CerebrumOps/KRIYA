# ==============================================================================
# KRIYA Authentication Backend Application
# ==============================================================================
# Dedicated on-premise authentication server for the KRIYA workbench.
# Runs on Port 5000, serving:
# - Multi-step corporate employee onboarding & registration
# - 2FA credential verification & JWT session issuance
# - Local SQLite directory mapping synchronized from the Raspberry Pi company database
# ==============================================================================

import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.api.auth_routes import router as auth_router
from backend.api.admin_routes import router as admin_router
from backend.database.auth_db import init_auth_db
from backend.database.sync_employees import sync_employees_from_company_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kriya.auth_backend")

app = FastAPI(
    title="KRIYA Enterprise Authentication Gateway",
    description="Sovereign Industrial AI Employee Directory & 2FA Auth Service",
    version="2.0.0"
)

# CORS configuration allowing requests from React web UI (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)


@app.on_event("startup")
async def on_startup():
    """Initializes local auth tables and synchronizes employee directory from company_db."""
    logger.info("Initializing local authentication SQLite database...")
    await init_auth_db()

    logger.info("Synchronizing employee directory from Raspberry Pi company database...")
    synced_count = await sync_employees_from_company_db()
    logger.info(f"Directory ready with {synced_count} mapped employee personas.")


@app.get("/health")
def health_check():
    """Health check endpoint probed by master runner and client UI."""
    return {
        "status": "ok",
        "service": "KRIYA Enterprise Authentication Gateway",
        "port": 5000,
        "version": "2.0.0"
    }
