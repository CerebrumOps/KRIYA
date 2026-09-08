# ==============================================================================
# KRIYA Tool: Terminal Command Execution
# ==============================================================================
# This tool allows KRIYA agents to run local shell commands safely and inspect
# files, directory listings, process status, and run system tasks.
#
# Style:
# 1. Tool function at top
# 2. OpenAI-compatible JSON schema below it
# ==============================================================================

import subprocess


# 1. The Actual Python Tool Function
def execute_terminal_command(command: str) -> str:
    """
    Executes a shell command on the local operating system
    and returns the stdout or stderr output as a string.
    """
    # Safety check: do not execute empty command
    if not command or not command.strip():
        return "[Error]: Command cannot be empty."

    try:
        # Run command with 30 seconds timeout to prevent hanging
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Combine stdout and stderr if any
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"

        # If nothing was output, return a friendly confirmation
        if not output.strip():
            return f"[Command executed successfully with return code {result.returncode} (no output)]"

        return output.strip()

    except subprocess.TimeoutExpired:
        return "[Error]: Command timed out after 30 seconds."
    except Exception as error:
        return f"[Error executing command]: {str(error)}"


# 2. OpenAI Function Tool Schema (Used by model to know how to call this tool)
TERMINAL_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_terminal_command",
        "description": "Execute a terminal or shell command locally on the system and return the output. Useful for checking files, directories, running scripts, and inspecting system state.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to run, for example: 'ls -la', 'cat filename.txt', 'uname -a', etc."
                }
            },
            "required": ["command"]
        }
    }
}
