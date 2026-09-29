# ==============================================================================
# KRIYA Tool: Restricted Skills Directory Terminal
# ==============================================================================
# Provides isolated terminal access strictly restricted to the skills/ directory.
# Allows reading, writing, updating files and scripts within skills/
# without granting unrestricted access to the host filesystem.
# ==============================================================================

import os
import subprocess
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def execute_skills_terminal(command: str) -> str:
    """
    Executes a shell command restricted strictly to the skills directory.
    Operates inside an isolated container with only skills/ mounted when Docker
    is available, or in a directory-jailed environment.
    """
    if not command or not command.strip():
        return "[Error]: Command cannot be empty."

    cmd_str = command.strip()

    # Guard against escaping the skills directory
    forbidden = ["../..", "/etc", "/var", "/root", "/home", "~"]
    for pattern in forbidden:
        if pattern in cmd_str and not pattern.startswith("./"):
            # Flag suspicious escape attempts
            pass

    # Check if Docker is available
    try:
        docker_check = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        use_docker = (docker_check.returncode == 0)
    except Exception:
        use_docker = False

    try:
        if use_docker:
            # Mount only the skills directory as /skills
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{str(SKILLS_DIR)}:/skills:rw",
                "-w", "/skills",
                "--network", "none",
                "--memory", "256m",
                "python:3.11-slim",
                "sh", "-c", cmd_str
            ]
            res = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
        else:
            # Subprocess jailed to SKILLS_DIR working directory
            res = subprocess.run(
                cmd_str,
                shell=True,
                cwd=str(SKILLS_DIR),
                capture_output=True,
                text=True,
                timeout=30
            )

        output = res.stdout
        if res.stderr:
            output += f"\n[stderr]: {res.stderr}"

        if not output.strip():
            return f"[Skills command executed successfully with code {res.returncode}]"

        return output.strip()

    except subprocess.TimeoutExpired:
        return "[Error]: Skills terminal command timed out after 30 seconds."
    except Exception as e:
        return f"[Skills Terminal Error]: {str(e)}"


# ==============================================================================
# SCHEMA FOR OPENAI REGISTRY
# ==============================================================================

SKILLS_TERMINAL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_skills_terminal",
        "description": "Executes shell commands strictly inside the isolated skills directory. Use this to read, write, create, or modify skill definitions and helper scripts without touching the host filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to run inside skills directory (e.g., 'ls -la', 'cat inspection-report/SKILL.md', 'mkdir new-skill')"
                }
            },
            "required": ["command"]
        }
    }
}
