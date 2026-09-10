# ==============================================================================
# KRIYA - Orchestration Main Entry
# ==============================================================================
# Coordinates the agentic workflow by linking:
# - loop.py: Multi-step agent loop with reasoning and tools
# - tool_handler.py: Tool execution logic
#
# Provides the clean functions used by webchat routes to stream to the frontend:
# 1. stream_kriya_chat: Streams agent tokens and tool events to the frontend
# 2. generate_kriya_chat: Non-streaming complete response generator
# ==============================================================================

import sys
from pathlib import Path
from typing import Any, Dict, Generator

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.schemas.webchat import WebChatRequest
from backend.orchestration.loop import run_agent_loop_stream, run_agent_loop
from backend.orchestration.tool_handler import handle_single_tool_call


def stream_kriya_chat(chat_request: WebChatRequest) -> Generator[str, None, None]:
    """
    Called by backend/api/webchat_routes.py.
    Forwards the user's webchat request into our multi-step agent loop
    and yields streaming tokens, reasoning tags, and tool events to the frontend.
    """
    return run_agent_loop_stream(
        user_message=chat_request.user_message,
        history=chat_request.history,
        thinking=bool(chat_request.thinking),
        model=chat_request.model or "default",
        temperature=chat_request.temperature if chat_request.temperature is not None else 0.2
    )


def generate_kriya_chat(chat_request: WebChatRequest) -> Dict[str, Any]:
    """
    Called by backend/api/webchat_routes.py for non-streaming requests.
    Returns the complete text output and generation metadata (tokens, time).
    """
    return run_agent_loop(
        user_message=chat_request.user_message,
        history=chat_request.history,
        thinking=bool(chat_request.thinking),
        model=chat_request.model or "default",
        temperature=chat_request.temperature if chat_request.temperature is not None else 0.2
    )
