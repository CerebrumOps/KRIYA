# ==============================================================================
# KRIYA - Backend Server Runner
# ==============================================================================
# Runs the FastAPI backend server using configuration loaded from .env.
# Does NOT use port 8000 (load balancer) or 8080 (llama-server).
#
# Usage:
#   python backend/run_backend.py
#   OR from inside backend directory:
#   python run_backend.py
# ==============================================================================

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Ensure the project root directory is in sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent if current_dir.name == "backend" else current_dir
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

PORT = int(os.getenv("BACKEND_PORT"))
HOST = os.getenv("BACKEND_HOST")
BACKEND_URL = os.getenv("BACKEND_URL")


def main():
    print("=" * 60)
    print(f"  Starting KRIYA Backend Server on {BACKEND_URL}")
    print(f"  Swagger Docs: {BACKEND_URL}/docs")
    print(f"  Health Check: {BACKEND_URL}/health")
    print("=" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=True
    )


if __name__ == "__main__":
    main()
