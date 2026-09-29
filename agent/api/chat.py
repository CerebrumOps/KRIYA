# ==============================================================================
# KRIYA API: Chat Streaming & Non-Streaming
# ==============================================================================
# Endpoints:
#   - POST /api/chat/stream
#   - POST /api/chat
#
# Rule: Each endpoint method is followed immediately by its request/response schemas.
# ==============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent.api.session import get_optional_session
from agent.orchestration.loop import run_agent_loop, run_agent_loop_stream
from agent.workspace.workspace_manager import set_active_workspace

router = APIRouter(prefix="/api/chat", tags=["WebChat"])


# ==============================================================================
# 1. STREAMING CHAT
# ==============================================================================

@router.post("/stream")
def chat_stream(
    request: "WebChatRequest",
    session: Optional[Dict[str, Any]] = Depends(get_optional_session),
):
    """
    Streams response tokens to the web frontend using chunked transfer.
    Streams <think>, <tool_call>, <tool_result>, and text tokens in real time.
    """
    employee_id = session.get("employee_id") if session else None

    def token_generator():
        try:
            set_active_workspace(employee_id, request.conversation_id)
            for token in run_agent_loop_stream(
                user_message=request.user_message,
                history=request.history,
                thinking=bool(request.thinking),
                model=request.model or "default",
                temperature=request.temperature if request.temperature is not None else 0.2
            ):
                yield token
        except Exception as e:
            yield f"\n[Error connecting to model server: {str(e)}]"

    return StreamingResponse(
        token_generator(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


class WebChatMessage(BaseModel):
    """A single message exchanged between user and KRIYA."""
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Text message content")


class WebChatRequest(BaseModel):
    """Business logic schema for chat requests coming from the web UI."""
    user_message: str = Field(..., description="The query or message typed by user")
    history: Optional[List[WebChatMessage]] = Field(default_factory=list, description="Prior conversation messages")
    thinking: Optional[bool] = Field(default=False, description="Toggle reasoning/thinking mode")
    model: Optional[str] = Field(default="default", description="Target model tag")
    temperature: Optional[float] = Field(default=0.2, description="Sampling temperature")
    conversation_id: Optional[str] = Field(default=None, description="Active conversation ID")


# ==============================================================================
# 2. NON-STREAMING CHAT
# ==============================================================================

@router.post("")
def chat_non_stream(
    request: WebChatRequest,
    session: Optional[Dict[str, Any]] = Depends(get_optional_session),
):
    """
    Non-streaming endpoint returning full response in JSON format.
    """
    employee_id = session.get("employee_id") if session else None
    set_active_workspace(employee_id, request.conversation_id)

    result = run_agent_loop(
        user_message=request.user_message,
        history=request.history,
        thinking=bool(request.thinking),
        model=request.model or "default",
        temperature=request.temperature if request.temperature is not None else 0.2
    )

    return WebChatResponse(
        reply=result["reply"],
        model_used=request.model or "default",
        status="success",
        tokens_generated=result.get("tokens_generated"),
        time_taken_ms=result.get("time_taken_ms"),
        speed_tokens_per_second=result.get("speed_tokens_per_second"),
        prompt_tokens=result.get("prompt_tokens")
    )


class WebChatResponse(BaseModel):
    """Business logic schema for non-streamed responses."""
    reply: str = Field(..., description="Generated text answer from KRIYA")
    model_used: str = Field(..., description="The model that produced the answer")
    status: str = Field(default="success", description="Status code or indicator")
    tokens_generated: Optional[int] = Field(default=None, description="Count of tokens generated")
    time_taken_ms: Optional[float] = Field(default=None, description="Generation time in ms")
    speed_tokens_per_second: Optional[float] = Field(default=None, description="Generation speed in tokens/sec")
    prompt_tokens: Optional[int] = Field(default=None, description="Prompt tokens evaluated")
