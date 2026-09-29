# ==============================================================================
# KRIYA Tool: Terminal Command Execution
# ==============================================================================
# This tool allows KRIYA agents to run shell commands inside their dedicated
# Linux OS environment with full root access. The agent can install packages
# (apt, pip), write files, run scripts, compile code, and manage processes.
#
# Style:
# 1. Tool function at top
# 2. OpenAI-compatible JSON schema below it
# ==============================================================================

import os
from pathlib import Path
import subprocess
from typing import Optional


# 1. The Actual Python Tool Function
def execute_terminal_command(command: str, cwd: Optional[str] = None) -> str:
    """
    Executes a shell command inside the dedicated Linux environment
    with full root privileges and returns stdout/stderr as a string.
    """
    # Safety check: do not execute empty command
    if not command or not command.strip():
        return "[Error]: Command cannot be empty."

    # Resolve working directory if specified, defaulting to active chat workspace
    work_dir = None
    if cwd and cwd.strip():
        work_path = Path(cwd.strip()).expanduser()
        if work_path.exists() and work_path.is_dir():
            work_dir = str(work_path)
        else:
            return f"[Error]: Specified working directory does not exist: {cwd}"
    else:
        try:
            from agent.workspace.workspace_manager import get_active_workspace_dir
            active_ws = get_active_workspace_dir()
            if active_ws and active_ws.exists():
                work_dir = str(active_ws)
        except Exception:
            pass

    try:
        # Run command with 120 seconds timeout to accommodate package installs or compiles
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=work_dir
        )

        # Combine stdout and stderr if any
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"

        # If nothing was output, return confirmation
        if not output.strip():
            return f"[Command executed successfully with return code {result.returncode} (no output)]"

        return output.strip()

    except subprocess.TimeoutExpired:
        return "[Error]: Command timed out after 120 seconds."
    except Exception as error:
        return f"[Error executing command]: {str(error)}"


# 2. OpenAI Function Tool Schema (Used by model to know how to call this tool)
TERMINAL_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_terminal_command",
        "description": (
            "Execute a shell command inside your dedicated Linux OS environment. "
            "You have full root access. You can install packages (apt, pip), "
            "write files, run scripts, compile code, inspect directories, manage processes, "
            "and perform any system operation. This is YOUR operating system."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run, for example: 'apt update', 'pip install pandas', 'ls -la', 'python3 script.py'."
                },
                "cwd": {
                    "type": "string",
                    "description": "Optional working directory in which to execute the command."
                }
            },
            "required": ["command"]
        }
    }
}
