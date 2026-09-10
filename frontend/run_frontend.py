#!/usr/bin/env python3
# ==============================================================================
# KRIYA - Frontend Server Runner
# ==============================================================================
# Launches the Vite React frontend development server on port 3000.
# Avoids ports 8000 and 8080 (reserved for LLM load balancer / inference node).
#
# Usage:
#   python frontend/run_frontend.py
#   OR
#   cd frontend && npm run dev
# ==============================================================================

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    frontend_dir = Path(__file__).resolve().parent
    port = os.getenv("FRONTEND_PORT", "3000")

    npm_bin = shutil.which("npm")
    if not npm_bin:
        mise_npm = Path("/home/vicky/.local/share/mise/installs/node/26.5.0/bin/npm")
        if mise_npm.exists():
            npm_bin = str(mise_npm)
        else:
            print("[Error] 'npm' not found on PATH. Please install Node.js.")
            sys.exit(1)

    print("=" * 60)
    print(f"  Starting KRIYA React/Vite Frontend on port {port}")
    print(f"  Open in browser: http://localhost:{port}")
    print("=" * 60)

    cmd = [npm_bin, "run", "dev", "--", "--port", port]
    try:
        subprocess.run(cmd, cwd=str(frontend_dir), check=True)
    except KeyboardInterrupt:
        print("\nStopping frontend server...")


if __name__ == "__main__":
    main()
