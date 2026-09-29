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

DEFAULT_WS = Path(__file__).resolve().parent.parent.parent / "workspace"
BASE_WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", str(DEFAULT_WS)))
BASE_WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# ContextVar storing the active workspace path for current async execution
_current_workspace_var: ContextVar[Path] = ContextVar(
    "_current_workspace_var",
    default=BASE_WORKSPACE_DIR
)
_current_employee_var: ContextVar[Optional[str]] = ContextVar(
    "_current_employee_var",
    default=None
)
_current_chat_var: ContextVar[Optional[str]] = ContextVar(
    "_current_chat_var",
    default=None
)


# Global fallbacks to ensure context across thread/generator boundaries
_last_active_workspace_dir: Path = BASE_WORKSPACE_DIR
_last_active_employee: Optional[str] = None
_last_active_chat: Optional[str] = None


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
    Primary Path: workspace/chats/{chat_id}/ (with user sub-mapping in workspace/users/{employee_id}/{chat_id}/)
    """
    chat = sanitize_path_segment(chat_id, "default_chat")
    emp = sanitize_path_segment(employee_id, "default_user")

    # Primary dedicated chat directory
    chat_dir = BASE_WORKSPACE_DIR / "chats" / chat
    chat_dir.mkdir(parents=True, exist_ok=True)

    # Subdirectories for organized artifacts
    (chat_dir / "documents").mkdir(exist_ok=True)
    (chat_dir / "media").mkdir(exist_ok=True)
    (chat_dir / "sandbox").mkdir(exist_ok=True)

    # User-scoped fallback directory for multi-tenant isolation
    user_ws_dir = BASE_WORKSPACE_DIR / "users" / emp / chat
    user_ws_dir.mkdir(parents=True, exist_ok=True)

    return chat_dir


def set_active_workspace(
    employee_id: Optional[str] = None,
    chat_id: Optional[str] = None
) -> Path:
    """
    Sets the active workspace for the current execution context and returns its path.
    """
    global _last_active_workspace_dir, _last_active_employee, _last_active_chat
    ws_dir = get_chat_workspace_dir(employee_id, chat_id)
    _current_workspace_var.set(ws_dir)
    _last_active_workspace_dir = ws_dir

    if employee_id:
        _current_employee_var.set(employee_id)
        _last_active_employee = employee_id
    if chat_id:
        _current_chat_var.set(chat_id)
        _last_active_chat = chat_id
    return ws_dir


def get_active_workspace_dir() -> Path:
    """
    Retrieves the active workspace directory for current context.
    Falls back to last active workspace or base workspace.
    """
    try:
        val = _current_workspace_var.get()
        if val == BASE_WORKSPACE_DIR and _last_active_workspace_dir != BASE_WORKSPACE_DIR:
            return _last_active_workspace_dir
        return val
    except Exception:
        return _last_active_workspace_dir or BASE_WORKSPACE_DIR


def get_active_employee_id() -> Optional[str]:
    """Returns the currently active employee_id for the execution context."""
    try:
        return _current_employee_var.get() or _last_active_employee
    except Exception:
        return _last_active_employee


def get_active_chat_id() -> Optional[str]:
    """Returns the currently active chat_id for the execution context."""
    try:
        return _current_chat_var.get() or _last_active_chat
    except Exception:
        return _last_active_chat

def get_file_category(filename: str) -> str:
    """Categorizes a file into 'documents', 'media', or 'sandbox' based on extension."""
    if not filename:
        return 'documents'
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.docx', '.xlsx', '.pptx', '.pdf', '.txt']:
        return 'documents'
    elif ext in ['.png', '.jpg', '.jpeg', '.bmp']:
        return 'media'
    elif ext in ['.py', '.csv', '.log', '.json']:
        return 'sandbox'
    return 'documents'
