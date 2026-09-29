# ==============================================================================
# KRIYA - Sovereign Industrial AI Agent Appliance
# ==============================================================================
# Local FastAPI application serving the sovereign agent harness, chat streaming,
# SQLite conversation history, per-chat workspaces, and tool execution.
# Operates directly within the dedicated container OS.
# ==============================================================================

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Ensure project root directory is on Python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from agent.api.chat import router as chat_router
from agent.api.conversations import router as conversation_router
from agent.api.workspace import router as workspace_router
from agent.api.settings import router as settings_router
from agent.database.sqlite_db import init_sqlite_db

app = FastAPI(
    title="KRIYA - Sovereign AI Agent Appliance",
    description="Dedicated On-Premise Industrial AI Harness & Local Execution Environment",
    version="2.0.0"
)

# Enable CORS for frontend and local network requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include agent and conversation routers
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(workspace_router)
app.include_router(settings_router)


@app.on_event("startup")
async def on_startup():
    """Initializes local SQLite tables and per-chat directories."""
    await init_sqlite_db()


# Lightweight stub for frontend compatibility
@app.get("/api/plan/active")
def get_active_plan_stub():
    return {"plan": None}


# Mount frontend dist assets if present
FRONTEND_DIST_PATH = root_dir / "frontend" / "dist"
FRONTEND_DIST_INDEX = FRONTEND_DIST_PATH / "index.html"
FRONTEND_DEV_INDEX = root_dir / "frontend" / "index.html"

if (FRONTEND_DIST_PATH / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_PATH / "assets")), name="assets")


@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def serve_ui():
    """Serves the single-page React frontend if bundled."""
    if FRONTEND_DIST_INDEX.exists():
        with open(FRONTEND_DIST_INDEX, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    elif FRONTEND_DEV_INDEX.exists():
        with open(FRONTEND_DEV_INDEX, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>KRIYA Sovereign AI Workbench - Frontend ready for deployment.</h2>", status_code=200)


@app.get("/health")
def health_check():
    """Health status probe for local monitor and reverse proxies."""
    return {"status": "ok", "service": "KRIYA Agent Appliance", "version": "2.0.0"}
