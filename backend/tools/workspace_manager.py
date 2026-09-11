# ==============================================================================
# KRIYA - User & Chat-Scoped Workspace Manager
# ==============================================================================
# Provides isolated on-premise workspace directories per employee and per chat.
# Directory structure:
#   workspace/users/{employee_id}/{chat_id}/
# ==============================================================================

import os
import re
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

BASE_WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent / "workspace"
BASE_WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# ContextVar storing the active workspace path for current async execution
_current_workspace_var: ContextVar[Path] = ContextVar(
    "_current_workspace_var",
    default=BASE_WORKSPACE_DIR
)


def sanitize_path_segment(val: Optional[str], default: str) -> str:
    """Sanitizes user/chat IDs to safe alphanumeric strings for filesystem directories."""
    if not val:
        return default
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', val.strip())
    return cleaned if cleaned else default


def get_chat_workspace_dir(
    employee_id: Optional[str] = None,
    chat_id: Optional[str] = None
) -> Path:
    """
    Returns (and creates if not present) the isolated workspace directory for a specific
    employee account and conversation thread.
    Path: workspace/users/{employee_id}/{chat_id}/
    """
    emp = sanitize_path_segment(employee_id, "default_user")
    chat = sanitize_path_segment(chat_id, "default_chat")

    ws_dir = BASE_WORKSPACE_DIR / "users" / emp / chat
    ws_dir.mkdir(parents=True, exist_ok=True)
    return ws_dir


def set_active_workspace(
    employee_id: Optional[str] = None,
    chat_id: Optional[str] = None
) -> Path:
    """
    Sets the active workspace for the current execution context and returns its path.
    """
    ws_dir = get_chat_workspace_dir(employee_id, chat_id)
    _current_workspace_var.set(ws_dir)
    return ws_dir


def get_active_workspace_dir() -> Path:
    """
    Retrieves the active workspace directory for current context.
    Falls back to base workspace if none set.
    """
    return _current_workspace_var.get()
