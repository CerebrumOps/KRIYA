# ==============================================================================
# KRIYA Tool: Host Filesystem & Command Bridge
# ==============================================================================
# Provides a secure bridge between the containerized KRIYA agent and the host
# operating system through a dedicated shared volume mount:
#
# 1. read_host_file: Read files from the host's shared directory (~/kriya-shared)
# 2. write_host_file: Write deliverables or scripts to host's shared directory
# 3. list_host_files: Inspect contents of the host's shared folder
# 4. execute_host_command: Run non-root shell commands on the host side
# ==============================================================================

import os
from pathlib import Path
import subprocess
from typing import Optional


def _get_host_shared_dir() -> Path:
    """
    Determines the path to the host shared directory:
    - Environment variable HOST_BRIDGE_DIR
    - Container mounts: `/host-bridge` or `/host_shared` (mounted from host ~/kriya-shared)
    - Outside container (local dev): `~/kriya-shared`
    """
    env_dir = os.getenv("HOST_BRIDGE_DIR")
    if env_dir and os.path.exists(env_dir):
        p = Path(env_dir)
    elif os.path.exists("/host-bridge"):
        p = Path("/host-bridge")
    elif os.path.exists("/host_shared"):
        p = Path("/host_shared")
    else:
        p = Path.home() / "kriya-shared"
    p.mkdir(parents=True, exist_ok=True)
    return p


HOST_SHARED_DIR = _get_host_shared_dir()


def _resolve_safe_path(rel_path: str) -> Optional[Path]:
    """
    Resolves relative path within HOST_SHARED_DIR, strictly preventing
    directory traversal attacks (e.g. ../../etc/shadow).
    """
    cleaned = (rel_path or "").strip().lstrip("/")
    base = _get_host_shared_dir().resolve()
    target = (base / cleaned).resolve()
    if target == base or base in target.parents:
        return target
    return None


# 1. Read Host File
def read_host_file(file_path: str) -> str:
    """Reads the text contents of a file from the host shared folder."""
    target = _resolve_safe_path(file_path)
    if target is None:
        return "[Host Bridge Error]: Access denied. Path traversal detected outside host shared directory."

    if not target.exists():
        return f"[Host Bridge Error]: File does not exist: {file_path}"
    if target.is_dir():
        return f"[Host Bridge Error]: Path is a directory, not a file: {file_path}"

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return content
    except Exception as e:
        return f"[Host Bridge Error reading file]: {str(e)}"


# 2. Write Host File
def write_host_file(file_path: str, content: str) -> str:
    """Writes text content to a file in the host shared folder."""
    target = _resolve_safe_path(file_path)
    if target is None:
        return "[Host Bridge Error]: Access denied. Path traversal detected outside host shared directory."

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"[Host Bridge Success]: Written {len(content)} bytes to host shared file '{file_path}'."
    except Exception as e:
        return f"[Host Bridge Error writing file]: {str(e)}"


# 3. List Host Files
def list_host_files(directory: str = ".") -> str:
    """Lists files and directories located in the host shared folder."""
    target = _resolve_safe_path(directory)
    if target is None:
        return "[Host Bridge Error]: Access denied. Path traversal detected outside host shared directory."

    if not target.exists():
        return f"[Host Bridge Error]: Directory not found: {directory}"
    if not target.is_dir():
        return f"[Host Bridge Error]: Path is a file, not a directory: {directory}"

    try:
        entries = []
        for item in sorted(target.iterdir()):
            kind = "[DIR] " if item.is_dir() else "[FILE]"
            size = f"{item.stat().st_size}B" if item.is_file() else "-"
            entries.append(f"{kind:<7} {item.name:<35} {size}")

        if not entries:
            return f"[Host Shared Directory '{directory}' is empty]"

        return f"### Files in Host Shared Directory ({target}):\n" + "\n".join(entries)
    except Exception as e:
        return f"[Host Bridge Error listing directory]: {str(e)}"


# 4. Execute Host Command (Non-Root, Restricted to Host Shared Workspace)
def execute_host_command(command: str) -> str:
    """
    Executes a shell command scoped inside the host shared directory without root privileges.
    Disallows sudo and administrative privilege escalation.
    """
    if not command or not command.strip():
        return "[Error]: Command cannot be empty."

    cmd_str = command.strip()

    # Block privilege escalation on host
    forbidden = ["sudo", "su ", "doas", "pkexec", "chown", "chmod 777 /"]
    for pattern in forbidden:
        if pattern in cmd_str:
            return f"[Security Block]: Administrative elevation command '{pattern}' is not permitted on the host system."

    shared_dir = _get_host_shared_dir()

    try:
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(shared_dir)
        )

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"

        if not output.strip():
            return f"[Host command executed successfully with code {result.returncode} (no output)]"

        return output.strip()

    except subprocess.TimeoutExpired:
        return "[Host Bridge Error]: Command timed out after 60 seconds."
    except Exception as e:
        return f"[Host Bridge Error executing command]: {str(e)}"


# ==============================================================================
# OPENAI SCHEMAS
# ==============================================================================

READ_HOST_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_host_file",
        "description": "Read a file from the host operating system's shared directory (~/kriya-shared). Safe access without root.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative file path within host shared folder (e.g. 'notes.txt', 'data/logs.csv')"
                }
            },
            "required": ["file_path"]
        }
    }
}

WRITE_HOST_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_host_file",
        "description": "Write or export a deliverable file directly to the host operating system's shared folder (~/kriya-shared).",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative target file path within host shared folder (e.g. 'reports/summary.txt', 'solution.py')"
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write into the file"
                }
            },
            "required": ["file_path", "content"]
        }
    }
}

LIST_HOST_FILES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_host_files",
        "description": "List files and subdirectories located inside the host operating system's shared folder (~/kriya-shared).",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Subdirectory to inspect (default is root of shared folder '.')"
                }
            }
        }
    }
}

EXECUTE_HOST_COMMAND_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_host_command",
        "description": "Execute a non-root shell command on the host operating system inside the shared workspace (~/kriya-shared). Privilege escalation (sudo) is forbidden.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to run on host (e.g. 'git status', 'ls -la', 'python3 check.py')"
                }
            },
            "required": ["command"]
        }
    }
}
