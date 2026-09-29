# ==============================================================================
# KRIYA API: Workspace Deliverables & File Management
# ==============================================================================
# Endpoints:
#   - GET /api/workspace/deliverables
#   - GET /api/workspace/download/{chat_id}/{filename}
#
# Rule: Each endpoint method is followed immediately by its request/response schemas.
# ==============================================================================

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from agent.api.session import get_optional_session
from agent.workspace.workspace_manager import BASE_WORKSPACE_DIR, get_chat_workspace_dir

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


# ==============================================================================
# 1. LIST DELIVERABLES
# ==============================================================================

@router.get("/deliverables")
async def list_workspace_deliverables(
    chat_id: Optional[str] = Query(None),
    session: Optional[Dict[str, Any]] = Depends(get_optional_session),
):
    """
    Lists all generated deliverable files for the authenticated user and current chat.
    Reads from workspace/users/{employee_id}/{chat_id}/ and categorized folders.
    """
    employee_id = session.get("employee_id") if isinstance(session, dict) else "default_user"
    target_chat = chat_id or "default_chat"

    ws_dir = get_chat_workspace_dir(employee_id, target_chat)
    ws_dir.mkdir(parents=True, exist_ok=True)

    deliverables = []
    seen_filenames = set()

    candidate_dirs = [ws_dir, BASE_WORKSPACE_DIR]

    try:
        for cdir in candidate_dirs:
            if not cdir.exists():
                continue
            raw_entries = []
            for f in cdir.iterdir():
                if f.is_file() and not f.name.startswith("."):
                    raw_entries.append(f)
            for cat in ["documents", "media", "sandbox"]:
                cat_dir = cdir / cat
                if cat_dir.exists():
                    for f in cat_dir.iterdir():
                        if f.is_file() and not f.name.startswith("."):
                            raw_entries.append(f)

            entries = sorted(
                raw_entries,
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            for entry in entries:
                if entry.name.endswith(".tmp") or entry.name.endswith(".pyc") or entry.name in seen_filenames:
                    continue
                ext = entry.suffix.lstrip(".").lower()
                if ext not in ["docx", "xlsx", "pptx", "csv", "pdf", "json", "py", "png", "txt"]:
                    continue

                seen_filenames.add(entry.name)
                stat = entry.stat()
                clean_title = entry.stem.replace("_", " ").replace("-", " ").title()

                deliverables.append({
                    "id": f"{target_chat}_{entry.name}",
                    "name": entry.name,
                    "type": ext if ext in ["docx", "xlsx", "pptx", "csv", "pdf", "json", "png", "py"] else "file",
                    "title": clean_title,
                    "description": TYPE_DESCRIPTIONS.get(ext, f"{ext.upper()} Deliverable Artifact"),
                    "size": format_size(stat.st_size),
                    "size_bytes": stat.st_size,
                    "generated_at": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %H:%M"),
                    "status": "verified",
                    "download_url": f"/api/workspace/download/{target_chat}/{entry.name}"
                })
    except Exception as e:
        return {"deliverables": [], "error": str(e)}

    return {"deliverables": deliverables}


class DeliverableItem(BaseModel):
    id: str
    name: str
    type: str
    title: str
    description: str
    size: str
    size_bytes: Optional[int] = None
    generated_at: str
    status: str = "verified"
    download_url: str


class WorkspaceDeliverablesResponse(BaseModel):
    deliverables: List[DeliverableItem] = Field(default_factory=list)


# ==============================================================================
# 2. DOWNLOAD DELIVERABLE FILE
# ==============================================================================

@router.get("/download/{chat_id}/{filename}")
async def download_workspace_file(
    chat_id: str,
    filename: str,
    session: Optional[Dict[str, Any]] = Depends(get_optional_session),
):
    """Securely serves a generated deliverable file for download."""
    employee_id = session.get("employee_id") if isinstance(session, dict) else "default_user"
    clean_filename = Path(filename).name

    ws_dir = get_chat_workspace_dir(employee_id, chat_id)
    target_file = ws_dir / clean_filename

    # Fallback checks in categorized subfolders
    if not target_file.is_file():
        for cat in ["documents", "media", "sandbox"]:
            cat_f = ws_dir / cat / clean_filename
            if cat_f.is_file():
                target_file = cat_f
                break

    # Fallback to BASE_WORKSPACE_DIR
    if not target_file.is_file():
        target_file = BASE_WORKSPACE_DIR / clean_filename
        if not target_file.is_file():
            for cat in ["documents", "media", "sandbox"]:
                cat_f = BASE_WORKSPACE_DIR / cat / clean_filename
                if cat_f.is_file():
                    target_file = cat_f
                    break

    # Recursive fallback
    if not target_file.is_file():
        for candidate in BASE_WORKSPACE_DIR.glob(f"**/{clean_filename}"):
            if candidate.is_file():
                target_file = candidate
                break

    if not target_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deliverable file '{clean_filename}' was not found in active workspace."
        )

    ext = target_file.suffix.lstrip(".").lower()
    media_type = MEDIA_TYPES.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(target_file),
        filename=clean_filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{clean_filename}"'
        }
    )
