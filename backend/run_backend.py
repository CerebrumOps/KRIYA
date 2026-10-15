#!/usr/bin/env python3
# ==============================================================================
# KRIYA Authentication Backend Launcher
# ==============================================================================
# Runs the independent Auth Gateway server on http://0.0.0.0:5000.
#
# Usage:
#   python backend/run_backend.py
# ==============================================================================

import os
import sys
from pathlib import Path
import uvicorn

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config import AUTH_HOST, AUTH_PORT


def main():
    print("=" * 68)
    print("  🛡️  KRIYA Enterprise Authentication Gateway")
    print("=" * 68)
    print(f"  🌐 Auth Server: http://{AUTH_HOST}:{AUTH_PORT}")
    print(f"  📄 Health Check: http://{AUTH_HOST}:{AUTH_PORT}/health")
    print("=" * 68)

    uvicorn.run(
        "backend.main:app",
        host=AUTH_HOST,
        port=AUTH_PORT,
        reload=True
    )


if __name__ == "__main__":
    main()
