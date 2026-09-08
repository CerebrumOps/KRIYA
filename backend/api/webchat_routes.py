import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.schemas.webchat import WebChatRequest, WebChatResponse
from backend.orchestration.main import stream_kriya_chat, generate_kriya_chat

router = APIRouter(prefix="/api/chat", tags=["WebChat"])


@router.post("/stream")
def chat_stream(request: WebChatRequest):
    """
    Streams response tokens to the web frontend using chunked transfer.
    """
    def token_generator():
        try:
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
def chat_non_stream(request: WebChatRequest):
    """
    Non-streaming endpoint returning full response in JSON format.
    """
    try:
        reply = generate_kriya_chat(request)
        return WebChatResponse(
            reply=reply,
            model_used=request.model or "default",
            status="success"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )
