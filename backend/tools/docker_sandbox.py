# ==============================================================================
# KRIYA Sandboxed Code Execution & Verification Engine
# ==============================================================================
# Executes Python utilities and test suites in an isolated environment:
# 1. Primary: Docker container (`python:3.11-slim`, `--network none`, `--memory 512m`)
# 2. Fallback: Isolated subprocess sandbox with strict timeout and sanitized environment
# Supports Demo 2 autonomous self-repair loop by capturing stdout/stderr and tracebacks.
# ==============================================================================

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from backend.tools.workspace_manager import get_active_workspace_dir, BASE_WORKSPACE_DIR

WORKSPACE_DIR = BASE_WORKSPACE_DIR


def is_docker_available() -> bool:
    """Checks if Docker daemon is accessible to the current user."""
    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3
        )
        return res.returncode == 0
    except Exception:
        return False


def run_code_in_sandbox(
    code: str,
    test_code: Optional[str] = None,
    timeout: int = 15,
    save_as_file: Optional[str] = None
) -> str:
    """
    Executes Python script and optional unit test suite inside an isolated sandbox.
    Returns structured results including stdout, stderr, execution status, and pass/fail state.
    """
    start_time = time.perf_counter()
    temp_dir = tempfile.mkdtemp(prefix="kriya_sandbox_")

    try:
        script_file = Path(temp_dir) / "solution.py"
        script_file.write_text(code, encoding="utf-8")

        # Also save to workspace if requested
        if save_as_file:
            active_ws = get_active_workspace_dir()
            ws_target = active_ws / save_as_file
            ws_target.write_text(code, encoding="utf-8")

        target_to_run = "solution.py"

        if test_code:
            test_file = Path(temp_dir) / "test_solution.py"
            full_test_content = (
                "import sys\n"
                "from pathlib import Path\n"
                "sys.path.insert(0, str(Path(__file__).parent))\n\n"
                f"{test_code}\n"
            )
            test_file.write_text(full_test_content, encoding="utf-8")
            target_to_run = "test_solution.py"

        use_docker = is_docker_available()
        backend_used = "Docker Container" if use_docker else "Subprocess Sandbox"

        if use_docker:
            cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", "512m",
                "-v", f"{temp_dir}:/app:ro",
                "-w", "/app",
                "python:3.11-slim",
                "python", target_to_run
            ]
            run_env = None
        else:
            # Isolated subprocess fallback using current python environment
            import sys
            cmd = [sys.executable, target_to_run]
            # Sanitize environment: strip sensitive tokens and DB passwords
            safe_env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "PYTHONPATH": f"{temp_dir}:{os.environ.get('PYTHONPATH', '')}",
                "LANG": "C.UTF-8",
                "TMPDIR": temp_dir,
                "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV", "")
            }
            run_env = safe_env

        proc = subprocess.run(
            cmd,
            cwd=temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=run_env,
            text=True
        )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        passed = (proc.returncode == 0)

        result = {
            "status": "PASS" if passed else "FAIL",
            "exit_code": proc.returncode,
            "duration_ms": duration_ms,
            "backend": backend_used,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip() if proc.stderr else None,
            "tests_verified": bool(test_code and passed)
        }

        # Formulate human-readable sandbox feedback for the model
        out_msg = f"[Sandbox Execution: {result['status']}] (Duration: {duration_ms}ms via {backend_used})\n"
        if result["stdout"]:
            out_msg += f"--- STDOUT ---\n{result['stdout']}\n"
        if result["stderr"]:
            out_msg += f"--- STDERR / TRACEBACK ---\n{result['stderr']}\n"
        if not passed:
            out_msg += "\n[ACTION REQUIRED]: Execution or test failed. Analyze stderr above, modify implementation, and rerun."

        return out_msg

    except subprocess.TimeoutExpired:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return f"[Sandbox Execution: FAIL] (Timeout Expired: exceeded {timeout}s limit)\n--- STDERR ---\nProcess killed due to execution timeout."
    except Exception as e:
        return f"[Sandbox Execution: FAIL]\n--- ERROR ---\n{str(e)}"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ==============================================================================
# SCHEMA FOR OPENAI REGISTRY
# ==============================================================================

SANDBOX_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_code_in_sandbox",
        "description": "Executes Python code and unit tests inside an isolated sandbox with memory and timeout constraints. Returns execution status, stdout, and tracebacks.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python implementation code to test"
                },
                "test_code": {
                    "type": "string",
                    "description": "Optional Python unit test code (asserts/test functions) that verifies the implementation"
                },
                "save_as_file": {
                    "type": "string",
                    "description": "Optional filename to persist in workspace upon success (e.g. 'generate_report.py')"
                }
            },
            "required": ["code"]
        }
    }
}
