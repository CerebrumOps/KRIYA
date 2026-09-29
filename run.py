#!/usr/bin/env python3
# ==============================================================================
# KRIYA - Sovereign Client Application Launcher (Local Dev Mode)
# ==============================================================================
# Starts both the local Agent API (:5001) and Vite Web UI (:3000) for local
# development outside Docker.
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
    print("  🚀 KRIYA Sovereign AI Workbench — Local Client Launcher")
    print("=" * 68)
    print(f"  🌐 Web Interface:      http://{FRONTEND_HOST}:{FRONTEND_PORT}")
    print(f"  🤖 Local Agent API:    http://{AGENT_HOST}:{AGENT_PORT}")
    print(f"  🛡️  Auth Gateway:       {AUTH_BACKEND_URL}")

    auth_ok = check_health(AUTH_BACKEND_URL)
    if auth_ok:
        print(f"  ✅ Auth Gateway:       ONLINE ({AUTH_BACKEND_URL}/health)")
    else:
        print(f"  ⚠️  Auth Gateway:       OFFLINE ({AUTH_BACKEND_URL})")
        print(f"     [Note] Start sih_backend if you need authentication:")
        print(f"            cd /home/vicky/Projects/sih_backend && python run_backend.py")
    print("=" * 68)
    print("  Press Ctrl+C at any time to cleanly stop all local services.\n")

    # 1. Start Agent API (:5001)
    agent_cmd = [
        sys.executable, "-m", "uvicorn",
        "agent.main:app",
        "--host", AGENT_HOST,
        "--port", str(AGENT_PORT),
        "--reload"
    ]
    agent_proc = subprocess.Popen(agent_cmd, cwd=str(ROOT_DIR), env=os.environ.copy())

    # Wait for Agent API
    time.sleep(1)

    # 2. Start Vite Frontend (:3000)
    frontend_dir = ROOT_DIR / "frontend"
    npm_cmd = "npm"
    fallback_npm = Path.home() / ".local/share/mise/installs/node/26.5.0/bin/npm"
    if fallback_npm.exists() and subprocess.run(["which", "npm"], capture_output=True).returncode != 0:
        npm_cmd = str(fallback_npm)

    cmd = [npm_cmd, "run", "dev", "--", "--host", FRONTEND_HOST, "--port", FRONTEND_PORT]
    frontend_proc = subprocess.Popen(cmd, cwd=str(frontend_dir), env=os.environ.copy())

    # Launch browser
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
    except KeyboardInterrupt:
        print("\n\nStopping KRIYA Client Services...")
    finally:
        for proc in [frontend_proc, agent_proc]:
            if proc and proc.poll() is None:
                try:
                    proc.send_signal(signal.SIGINT)
                    proc.wait(timeout=2)
                except Exception:
                    proc.kill()
        print("All client services stopped cleanly.\n")


if __name__ == "__main__":
    main()
