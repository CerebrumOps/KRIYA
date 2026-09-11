from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.schemas.webchat import WebChatRequest, WebChatResponse
from backend.orchestration.main import stream_kriya_chat, generate_kriya_chat
from backend.api.session import get_optional_session
from backend.tools.workspace_manager import set_active_workspace

router = APIRouter(prefix="/api/chat", tags=["WebChat"])


@router.post("/stream")
def chat_stream(
    request: WebChatRequest,
    session: Optional[Dict[str, Any]] = Depends(get_optional_session),
):
    """
    Streams response tokens to the web frontend using chunked transfer.
    """
    employee_id = session.get("employee_id") if session else None

    def token_generator():
        try:
            set_active_workspace(employee_id, request.conversation_id)
            for token in stream_kriya_chat(request):
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


@router.post("", response_model=WebChatResponse)
def chat_non_stream(
    request: WebChatRequest,
    session: Optional[Dict[str, Any]] = Depends(get_optional_session),
):
    """
    Non-streaming endpoint returning full response in JSON format.
    """
    employee_id = session.get("employee_id") if session else None
    set_active_workspace(employee_id, request.conversation_id)
    try:
        result = generate_kriya_chat(request)
        reply = result["reply"] if isinstance(result, dict) else str(result)
        tokens_gen = result.get("tokens_generated") if isinstance(result, dict) else None
        time_ms = result.get("time_taken_ms") if isinstance(result, dict) else None
        speed = result.get("speed_tokens_per_second") if isinstance(result, dict) else None
        prompt_tokens = result.get("prompt_tokens") if isinstance(result, dict) else None

        return WebChatResponse(
            reply=reply,
            model_used=request.model or "default",
            status="success",
            tokens_generated=tokens_gen,
            time_taken_ms=time_ms,
            speed_tokens_per_second=speed,
            prompt_tokens=prompt_tokens
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )
