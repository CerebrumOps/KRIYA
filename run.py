#!/usr/bin/env python3
# ==============================================================================
# KRIYA - Sovereign Client Application Launcher (Local Dev Mode)
# ==============================================================================
# Starts all client-side services:
# 1. Enterprise Auth Gateway (:5000)
# 2. Local Agent API (:5001)
# 3. React / Vite Web UI (:3000)
#
# Usage:
#   python run.py
# ==============================================================================

import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path)

FRONTEND_PORT = os.getenv("FRONTEND_PORT", "3000")
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "0.0.0.0")
AGENT_PORT = int(os.getenv("AGENT_PORT", "5001"))
AGENT_HOST = os.getenv("AGENT_HOST", "0.0.0.0")
AUTH_BACKEND_URL = os.getenv("AUTH_BACKEND_URL", "http://localhost:5000").rstrip("/")
AUTH_PORT = 5000

# Prefer virtualenv Python if present
VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
PYTHON_EXEC = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def check_health(url: str, timeout: float = 1.0) -> bool:
    """Probes health endpoint."""
    try:
        req = urllib.request.Request(f"{url}/health", headers={"User-Agent": "KRIYA-Check"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def main():
    print("=" * 68)
    print("  🚀 KRIYA Sovereign AI Workbench — Full Client Launcher")
    print("=" * 68)
    print(f"  🌐 Web Interface:      http://{FRONTEND_HOST}:{FRONTEND_PORT}")
    print(f"  🤖 Local Agent API:    http://{AGENT_HOST}:{AGENT_PORT}")
    print(f"  🛡️  Auth Gateway:       http://0.0.0.0:{AUTH_PORT}")
    print(f"  🐍 Python Runtime:     {PYTHON_EXEC}")
    print("=" * 68)

    auth_proc = None
    auth_ok = check_health(AUTH_BACKEND_URL)
    if auth_ok:
        print(f"  ✅ Auth Gateway:       ONLINE (Already running at {AUTH_BACKEND_URL})")
    else:
        print(f"  📦 Starting Auth Gateway on port {AUTH_PORT}...")
        auth_cmd = [
            PYTHON_EXEC, "-m", "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", str(AUTH_PORT)
        ]
        auth_proc = subprocess.Popen(auth_cmd, cwd=str(ROOT_DIR), env=os.environ.copy())

        # Wait for Auth Gateway readiness
        for _ in range(10):
            time.sleep(0.5)
            if check_health(AUTH_BACKEND_URL):
                print(f"  ✅ Auth Gateway:       ONLINE (http://localhost:{AUTH_PORT}/health)")
                break

    # 1. Start Agent API (:5001)
    print(f"  🤖 Starting Local Agent API on port {AGENT_PORT}...")
    agent_cmd = [
        PYTHON_EXEC, "-m", "uvicorn",
        "agent.main:app",
        "--host", AGENT_HOST,
        "--port", str(AGENT_PORT)
    ]
    agent_proc = subprocess.Popen(agent_cmd, cwd=str(ROOT_DIR), env=os.environ.copy())

    # Wait for Agent API
    time.sleep(1)

    # 2. Start Vite Frontend (:3000)
    print(f"  🌐 Starting Vite Web UI on port {FRONTEND_PORT}...")
    frontend_dir = ROOT_DIR / "frontend"
    npm_cmd = "npm"
    fallback_npm = Path.home() / ".local/share/mise/installs/node/26.5.0/bin/npm"
    if fallback_npm.exists() and subprocess.run(["which", "npm"], capture_output=True).returncode != 0:
        npm_cmd = str(fallback_npm)

    cmd = [npm_cmd, "run", "dev", "--", "--host", FRONTEND_HOST, "--port", FRONTEND_PORT]
    frontend_proc = subprocess.Popen(cmd, cwd=str(frontend_dir), env=os.environ.copy())

    print("\n  ✨ All KRIYA services launched!")
    print("  Press Ctrl+C at any time to cleanly stop all local services.\n")

    # Launch browser if supported
    time.sleep(1.5)
    target_url = f"http://localhost:{FRONTEND_PORT}"
    if sys.platform.startswith("linux"):
        subprocess.Popen(["xdg-open", target_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        while True:
            time.sleep(1)
            if frontend_proc.poll() is not None or agent_proc.poll() is not None:
                break
            if auth_proc and auth_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n\nStopping KRIYA Client Services...")
    finally:
        procs_to_stop = [frontend_proc, agent_proc]
        if auth_proc:
            procs_to_stop.append(auth_proc)
        for proc in procs_to_stop:
            if proc and proc.poll() is None:
                try:
                    proc.send_signal(signal.SIGINT)
                    proc.wait(timeout=2)
                except Exception:
                    proc.kill()
        print("All client services stopped cleanly.\n")


if __name__ == "__main__":
    main()
