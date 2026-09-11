import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Ensure root directory is on Python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.api.webchat_routes import router as webchat_router
from backend.api.conversation_routes import router as conversation_router
from backend.api.auth_routes import router as auth_router
from backend.api.company_routes import router as company_router
from backend.api.plan_routes import router as plan_router
from backend.api.admin_routes import router as admin_router
from backend.api.workspace_routes import router as workspace_router

app = FastAPI(
    title="KRIYA - Sovereign Industrial AI Workbench",
    description="On-Premise Multi-Agentic AI Workbench for Confidential Industrial Work",
    version="1.0.0"
)

# Enable CORS so any frontend (React, local dev, or HTML) can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(webchat_router)
app.include_router(conversation_router)
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(plan_router)
app.include_router(admin_router)
app.include_router(workspace_router)

# Mount frontend dist assets if present
FRONTEND_DIST_PATH = root_dir / "frontend" / "dist"
FRONTEND_DIST_INDEX = FRONTEND_DIST_PATH / "index.html"
FRONTEND_DEV_INDEX = root_dir / "frontend" / "index.html"

from fastapi.staticfiles import StaticFiles
if (FRONTEND_DIST_PATH / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_PATH / "assets")), name="assets")


@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def serve_ui():
    """Serves the single-page React frontend."""
    if FRONTEND_DIST_INDEX.exists():
        with open(FRONTEND_DIST_INDEX, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    elif FRONTEND_DEV_INDEX.exists():
        with open(FRONTEND_DEV_INDEX, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Frontend index.html not found yet.</h2>", status_code=404)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "KRIYA Backend"}
