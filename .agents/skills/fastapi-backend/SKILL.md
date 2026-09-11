---
name: fastapi-backend
description: Comprehensive skill for Python FastAPI backend development, asyncpg connection pooling, Pydantic v2 schemas, Server-Sent Events (SSE) streaming, air-gapped security, and high-performance API design. Use when writing, refactoring, or optimizing backend endpoints, database queries, and async pipelines.
---

# FastAPI Backend & Database Engineering Skill

This skill provides design patterns, architecture rules, and implementation standards for production-grade FastAPI and PostgreSQL backend services.

---

## 1. Core Architecture & Dependency Management

### A. Modular Project Layout
```text
backend/
├── api/                  # Route handlers (APIRouter instances)
├── database/             # Schemas (DDL) and asyncpg request queries
├── orchestration/        # Core agentic loops & LLM adapters
├── schemas/              # Pydantic v2 request/response models
├── tools/                # Local executable tool functions
└── main.py               # FastAPI app assembly, CORS, & lifespan
```

### B. Environment Decoupling
- Never hardcode hostnames, ports, passwords, or endpoints in code files.
- Always load from `.env` using `dotenv.load_dotenv(dotenv_path=env_path)`.
- When reading connection strings containing special characters (like `@` in passwords), URL-encode special characters (e.g. `@` -> `%40`).

---

## 2. PostgreSQL Connection Management (`asyncpg`)

### A. Global Connection Pool Pattern
Never open single one-off connections for every HTTP request. Use a global `asyncpg.Pool`:

```python
import os
import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None

async def get_db_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        db_url = os.getenv("DATABASE_URL")
        _pool = await asyncpg.create_pool(
            db_url,
            min_size=2,
            max_size=10,
            command_timeout=30
        )
    return _pool
```

### B. Safe Resource Acquisition
Always use `async with pool.acquire() as conn:` to automatically release connections back to the pool:

```python
async def query_equipment(tag: str) -> Optional[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, tag, status, metadata FROM equipment WHERE tag = $1",
            tag
        )
        return dict(row) if row else None
```

---

## 3. Real-Time Token Streaming (`StreamingResponse`)

For streaming LLM tokens, reasoning chunks, and tool events to the frontend:

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/stream")
def stream_chat(request: WebChatRequest):
    def event_generator():
        try:
            for chunk in agent_loop(request):
                yield chunk
        except Exception as exc:
            yield f"\n[Error: {str(exc)}]"

    return StreamingResponse(
        event_generator(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

---

## 4. Pydantic v2 Schema Best Practices

- Use `model_config = ConfigDict(from_attributes=True, populate_by_name=True)`.
- Use `Field(description=..., default=...)` for explicit OpenAPI documentation.
- When generating titles or metadata, strip trailing/leading punctuation and normalize strings.
