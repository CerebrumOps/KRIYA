# ==============================================================================
# KRIYA - Sovereign Engineering Memory Database (SQLite)
# ==============================================================================
# Manages persistent semantic storage and search for engineering insights,
# calculation logs, user preferences, and historical conversation transcripts.
# Uses local SQLite engine inside the client appliance.
# ==============================================================================

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent.database.sqlite_db import (
    execute_query,
    fetch_one,
    fetch_all,
    init_sqlite_db,
)


async def init_memory_db() -> None:
    """Ensures local tables are initialized."""
    await init_sqlite_db()


async def store_memory(
    employee_id: str,
    content: str,
    memory_type: str = "insight",
    conversation_id: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Stores an explicit engineering memory or user finding in local SQLite."""
    await init_memory_db()

    mem_id = f"mem_{uuid.uuid4().hex[:12]}"
    kw_json = json.dumps(keywords or [])
    meta_json = json.dumps(metadata or {})
    now_iso = datetime.utcnow().isoformat()

    sql = """
    INSERT INTO chat_memories (id, employee_id, conversation_id, content, memory_type, keywords, metadata, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    await execute_query(sql, (mem_id, employee_id, conversation_id, content, memory_type, kw_json, meta_json, now_iso))

    return {
        "id": mem_id,
        "employee_id": employee_id,
        "conversation_id": conversation_id,
        "content": content,
        "memory_type": memory_type,
        "keywords": keywords or [],
        "metadata": metadata or {}
    }


async def search_saved_memories(
    employee_id: str,
    query: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Searches saved technical memories using text matching."""
    await init_memory_db()

    pattern = f"%{query.strip().lower()}%"
    sql = """
    SELECT id, employee_id, content, memory_type, keywords, metadata, created_at
    FROM chat_memories
    WHERE employee_id = ? AND (LOWER(content) LIKE ? OR LOWER(keywords) LIKE ?)
    ORDER BY created_at DESC
    LIMIT ?
    """
    rows = await fetch_all(sql, (employee_id, pattern, pattern, limit))

    results = []
    for r in rows:
        kw = r.get("keywords", "[]")
        if isinstance(kw, str):
            try:
                kw = json.loads(kw)
            except Exception:
                kw = []
        results.append({
            "id": r["id"],
            "employee_id": r["employee_id"],
            "content": r["content"],
            "memory_type": r["memory_type"],
            "keywords": kw,
            "score": 0.85
        })
    return results


async def search_past_conversations(
    employee_id: str,
    query: str,
    current_conversation_id: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Searches past conversation messages for relevant engineering topics."""
    await init_memory_db()

    pattern = f"%{query.strip().lower()}%"
    sql = """
    SELECT id, name, messages, updated_at
    FROM conversations
    WHERE employee_id = ? AND LOWER(messages) LIKE ?
    ORDER BY updated_at DESC
    LIMIT ?
    """
    rows = await fetch_all(sql, (employee_id, pattern, limit * 2))

    results = []
    for r in rows:
        if current_conversation_id and r["id"] == current_conversation_id:
            continue
        msgs = r.get("messages", "[]")
        if isinstance(msgs, str):
            try:
                msgs = json.loads(msgs)
            except Exception:
                msgs = []
        for m in msgs:
            c = m.get("content", "")
            if query.lower() in c.lower():
                results.append({
                    "conversation_id": r["id"],
                    "conversation_title": r.get("name") or "Prior Session",
                    "role": m.get("role", "assistant"),
                    "excerpt": c[:300],
                    "score": 0.80
                })
                break
    return results[:limit]


async def list_recent_memories(employee_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Lists recent memories for employee."""
    await init_memory_db()
    sql = """
    SELECT id, employee_id, content, memory_type, keywords, created_at
    FROM chat_memories
    WHERE employee_id = ?
    ORDER BY created_at DESC
    LIMIT ?
    """
    return await fetch_all(sql, (employee_id, limit))
