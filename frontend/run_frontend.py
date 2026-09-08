# ==============================================================================
# KRIYA - Frontend Web Server Runner
# ==============================================================================
# Serves the single-page React frontend on port 3000 (avoids 8000 and 8080).
# Allows running the frontend independently on a separate laptop during demos.
#
# Usage:
#   python frontend/run_frontend.py
#   OR from inside frontend directory:
#   python run_frontend.py
# ==============================================================================

import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Locate frontend directory
current_dir = Path(__file__).resolve().parent
frontend_dir = current_dir if current_dir.name == "frontend" else current_dir / "frontend"

PORT = int(os.getenv("FRONTEND_PORT", 3000))
HOST = os.getenv("FRONTEND_HOST", "0.0.0.0")


class CustomFrontendHandler(SimpleHTTPRequestHandler):
    """Serves index.html by default for any root request."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(frontend_dir), **kwargs)


def main():
    print("=" * 60)
    print(f"  Starting KRIYA Frontend Server on http://{HOST}:{PORT}")
    print(f"  Open in browser: http://localhost:{PORT}")
    print("=" * 60)

    server = ThreadingHTTPServer((HOST, PORT), CustomFrontendHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping frontend server...")
        server.shutdown()


if __name__ == "__main__":
    main()
