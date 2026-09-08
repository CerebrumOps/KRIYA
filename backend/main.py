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

# Serve the single-file React HTML frontend directly from the server
FRONTEND_INDEX_PATH = root_dir / "frontend" / "index.html"


@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def serve_ui():
    """Serves the single-page React frontend."""
    if FRONTEND_INDEX_PATH.exists():
        with open(FRONTEND_INDEX_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Frontend index.html not found yet.</h2>", status_code=404)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "KRIYA Backend"}
