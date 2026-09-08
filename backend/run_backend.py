# ==============================================================================
# KRIYA - Backend Server Runner
# ==============================================================================
# Runs the FastAPI backend server on a dedicated port (default: 5000).
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
import uvicorn

# Ensure the project root directory is in sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent if current_dir.name == "backend" else current_dir
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Default port 5000 (avoids 8000 and 8080)
PORT = int(os.getenv("BACKEND_PORT", 5000))
HOST = os.getenv("BACKEND_HOST", "0.0.0.0")


def main():
    print("=" * 60)
    print(f"  Starting KRIYA Backend Server on http://{HOST}:{PORT}")
    print(f"  Swagger Docs: http://localhost:{PORT}/docs")
    print(f"  Health Check: http://localhost:{PORT}/health")
    print("=" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=True
    )


if __name__ == "__main__":
    main()
