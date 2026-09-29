# ==============================================================================
# KRIYA - Local SQLite Database Engine
# ==============================================================================
# Self-contained, zero-external-dependency local database for the KRIYA appliance.
# Stores conversation histories, message exchanges, and long-term memory embeddings.
# Runs inside the dedicated container OS, persisted via volume mount at /app/data/.
# ==============================================================================

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Locate data directory: env DATA_DIR -> /app/data or local ./data
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR_PATH = Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR)))
DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)

SQLITE_DB_PATH = DATA_DIR_PATH / "kriya_local.db"

_is_initialized = False
_lock = asyncio.Lock()


def get_db_path() -> Path:
    """Returns absolute path to the local SQLite database file."""
    return SQLITE_DB_PATH


def _get_connection() -> sqlite3.Connection:
    """Creates a configured connection with row factory and WAL mode."""
    conn = sqlite3.connect(str(SQLITE_DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _init_schema_sync() -> None:
    """Initializes tables and indexes synchronously."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            employee_id TEXT,
            messages TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations (updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_conversations_emp ON conversations (employee_id, updated_at DESC);

        CREATE TABLE IF NOT EXISTS chat_memories (
            id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            conversation_id TEXT,
            content TEXT NOT NULL,
            memory_type TEXT NOT NULL DEFAULT 'insight',
            keywords TEXT NOT NULL DEFAULT '[]',
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_chat_memories_emp ON chat_memories (employee_id);
        """)
        conn.commit()


async def init_sqlite_db() -> None:
    """Ensures database and required tables exist asynchronously."""
    global _is_initialized
    if _is_initialized:
        return
    async with _lock:
        if not _is_initialized:
            await asyncio.to_thread(_init_schema_sync)
            _is_initialized = True


def _run_query_sync(sql: str, params: tuple = ()) -> int:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount


def _fetch_one_sync(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def _fetch_all_sync(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


async def execute_query(sql: str, params: tuple = ()) -> int:
    """Executes an INSERT, UPDATE, or DELETE query asynchronously."""
    await init_sqlite_db()
    return await asyncio.to_thread(_run_query_sync, sql, params)


async def fetch_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """Fetches a single row as a dictionary asynchronously."""
    await init_sqlite_db()
    return await asyncio.to_thread(_fetch_one_sync, sql, params)


async def fetch_all(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Fetches all rows matching the query asynchronously."""
    await init_sqlite_db()
    return await asyncio.to_thread(_fetch_all_sync, sql, params)
