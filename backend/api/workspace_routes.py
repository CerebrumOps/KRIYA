# ==============================================================================
# KRIYA API Routes: Workspace Deliverables & File Management
# ==============================================================================
# Provides isolated endpoints for querying and downloading deliverables generated
# within a specific employee's active chat workspace (workspace/users/{employee_id}/{chat_id}/).
# ==============================================================================

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from backend.api.session import get_optional_session
from backend.tools.workspace_manager import get_chat_workspace_dir

router = APIRouter(prefix="/api/workspace", tags=["Workspace"])

MEDIA_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "pdf": "application/pdf",
    "csv": "text/csv; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "txt": "text/plain; charset=utf-8",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}

TYPE_DESCRIPTIONS = {
    "docx": "Official Technical Approval Note / Specification Document",
    "xlsx": "Cost Analysis / Financial Allocation Workbook",
    "pptx": "Executive Briefing / Management Slide Deck",
    "pdf": "Compiled Regulatory / Engineering Report",
    "csv": "Sensor Telemetry / Asset Integrity Dataset",
    "json": "Structured Parameter / Equipment Configuration Payload",
    "png": "Inspection Graphic / Technical Diagram",
    "jpg": "Inspection Photo / Visual Evidence Capture",
}


def format_size(size_bytes: int) -> str:
    """Formats file size into human-readable representation."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


@router.get("/deliverables")
async def list_workspace_deliverables(
    chat_id: Optional[str] = Query(None),
    session: Optional[Dict[str, Any]] = Depends(get_optional_session),
):
    """
    Lists all generated deliverable files for the authenticated user and current chat.
    Reads directly from workspace/users/{employee_id}/{chat_id}/.
    """
    employee_id = session.get("employee_id") if session else None
    if not employee_id or not chat_id:
        return {"deliverables": []}

    ws_dir = get_chat_workspace_dir(employee_id, chat_id)
    if not ws_dir.exists():
        return {"deliverables": []}

    deliverables = []
    try:
        entries = sorted(
            [f for f in ws_dir.iterdir() if f.is_file() and not f.name.startswith(".")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        for entry in entries:
            # Skip hidden, temporary or script files
            if entry.name.endswith(".tmp") or entry.name.endswith(".pyc"):
                continue

            stat = entry.stat()
            ext = entry.suffix.lstrip(".").lower()
            clean_title = entry.stem.replace("_", " ").replace("-", " ").title()

            deliverables.append({
                "id": f"{chat_id}_{entry.name}",
                "name": entry.name,
                "type": ext if ext in ["docx", "xlsx", "pptx", "csv", "pdf", "json", "png"] else "file",
                "title": clean_title,
                "description": TYPE_DESCRIPTIONS.get(ext, f"{ext.upper()} Deliverable Artifact"),
                "size": format_size(stat.st_size),
                "size_bytes": stat.st_size,
                "generated_at": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %H:%M"),
                "status": "verified",
                "download_url": f"/api/workspace/download/{chat_id}/{entry.name}"
            })
    except Exception as e:
        return {"deliverables": [], "error": str(e)}

    return {"deliverables": deliverables}


@router.get("/download/{chat_id}/{filename}")
async def download_workspace_file(
    chat_id: str,
    filename: str,
    session: Optional[Dict[str, Any]] = Depends(get_optional_session),
):
    """
    Securely serves a generated deliverable file for download from the user's chat workspace.
    Guards against path traversal attacks.
    """
    employee_id = session.get("employee_id") if session else None
    if not employee_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access deliverables."
        )

    ws_dir = get_chat_workspace_dir(employee_id, chat_id)
    target_file = (ws_dir / filename).resolve()

    # Prevent directory traversal attacks
    if not str(target_file).startswith(str(ws_dir.resolve())) or not target_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deliverable file '{filename}' was not found in chat workspace."
        )

    ext = target_file.suffix.lstrip(".").lower()
    media_type = MEDIA_TYPES.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(target_file),
        filename=filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
