#!/usr/bin/env python3
# ==============================================================================
# KRIYA - Unified Development Runner
# ==============================================================================
# Runs BOTH the Backend (Port 5000) and Frontend (Port 3000) concurrently
# from a single terminal during local development.
#
# Ports Used:
#   - Frontend UI:  http://localhost:3000
#   - Backend API:  http://localhost:5000
#   - Balancer:     http://100.98.154.51:8000 (Phone gateway)
#   (Ports 8000 and 8080 are strictly preserved for model server / balancer)
#
# Press Ctrl+C at any time to cleanly stop both services.
# ==============================================================================

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

# Locate Python binary (prefer active venv if present)
VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
PYTHON_EXEC = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def main():
    print("=" * 65)
    print("  🚀 Starting KRIYA Development Environment (Backend + Frontend)")
    print("=" * 65)
    print("  🌐 Frontend Web UI:    http://localhost:3000")
    print("  ⚙️  Backend FastAPI:   http://localhost:5000")
    print("  📚 API Documentation:  http://localhost:5000/docs")
    print("  📱 Phone LoadBalancer: http://100.98.154.51:8000")
    print("=" * 65)
    print("  [Tip] For multi-laptop demos, you can also run them separately:")
    print("        Laptop A (Backend):  python backend/run_backend.py")
    print("        Laptop B (Frontend): python frontend/run_frontend.py")
    print("=" * 65)
    print("  Press Ctrl+C to stop all services.\n")

    backend_script = ROOT_DIR / "backend" / "run_backend.py"
    frontend_script = ROOT_DIR / "frontend" / "run_frontend.py"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    # Launch Backend process
    backend_proc = subprocess.Popen(
        [PYTHON_EXEC, str(backend_script)],
        cwd=str(ROOT_DIR),
        env=env
    )

    # Give backend a moment to initialize
    time.sleep(0.5)

    # Launch Frontend process
    frontend_proc = subprocess.Popen(
        [PYTHON_EXEC, str(frontend_script)],
        cwd=str(ROOT_DIR),
        env=env
    )

    try:
        # Keep runner alive while child processes are running
        while True:
            time.sleep(1)
            # Check if any process exited unexpectedly
            if backend_proc.poll() is not None:
                print("\n[Alert] Backend process terminated.")
                break
            if frontend_proc.poll() is not None:
                print("\n[Alert] Frontend process terminated.")
                break
    except KeyboardInterrupt:
        print("\n\nStopping KRIYA services...")
    finally:
        # Gracefully terminate both processes
        for proc, name in [(frontend_proc, "Frontend"), (backend_proc, "Backend")]:
            if proc.poll() is None:
                try:
                    proc.send_signal(signal.SIGINT)
                    proc.wait(timeout=3)
                except Exception:
                    proc.kill()
        print("All KRIYA services stopped cleanly.\n")


if __name__ == "__main__":
    main()
