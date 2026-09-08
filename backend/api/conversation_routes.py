# ==============================================================================
# KRIYA API Routes: Conversation Management & Title Generation
# ==============================================================================
# Endpoints for creating chats, listing history for sidebar, loading chats,
# appending message exchanges to PostgreSQL, and the mini-agent title generator.
# ==============================================================================

import logging
import re
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from backend.database.kriya_db.request.conversation_db import (
    create_conversation,
    get_conversation,
    list_conversations,
    append_messages_to_conversation,
    update_conversation_name,
    delete_conversation,
)
from backend.schemas.conversation import (
    CreateConversationRequest,
    ConversationListItem,
    ConversationSummary,
    ConversationDetail,
    AppendExchangeRequest,
    GenerateTitleRequest,
    GenerateTitleResponse,
)
from backend.schemas.model_request import ModelRequest
from backend.api.model_client import send_async_chat_request
from backend.prompts.system_prompts.conversation_naming_sys import CONVERSATION_NAMING_SYSTEM_PROMPT

logger = logging.getLogger("kriya.api.conversations")

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


def parse_exchange_for_titling(user_message: str, raw_assistant_response: str) -> str:
    """
    Extracts the user prompt, AI reasoning (excluding tool call blocks),
    and clean final response, formatting them cleanly for the naming mini-agent.
    Tool schemas and raw tool call payloads are excluded to avoid clutter and hallucinations.
    """
    # 1. Extract reasoning thoughts (<think>...</think> content)
    think_matches = re.findall(r'<think>([\s\S]*?)</think>', raw_assistant_response)
    if think_matches:
        reasoning_text = " ".join(t.strip() for t in think_matches if t.strip())
    else:
        # Fallback if think tag was unclosed
        if "<think>" in raw_assistant_response:
            reasoning_text = raw_assistant_response.split("<think>")[-1].strip()
        else:
            reasoning_text = "Direct execution without extended thinking steps."

    # 2. Extract clean response by stripping tool calls, tool results, and think tags
    cleaned = re.sub(r'<tool_call[\s\S]*?</tool_call>', '', raw_assistant_response)
    cleaned = re.sub(r'<tool_result[\s\S]*?</tool_result>', '', cleaned)
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', cleaned)
    cleaned = re.sub(r'</?(tool_call|tool_result|think)[^>]*>', '', cleaned)
    response_text = cleaned.strip()

    if not response_text:
        response_text = "Action completed."

    # Format strictly as requested:
    # user :
    # KRIYA AI : 
    #    Reasoning :
    #    Response :
    return (
        f"user :\n{user_message.strip()}\n\n"
        f"KRIYA AI : \n"
        f"   Reasoning :\n   {reasoning_text[:1200]}\n\n"
        f"   Response :\n   {response_text[:1200]}"
    )


@router.post("", response_model=ConversationDetail)
async def create_new_conversation(payload: Optional[CreateConversationRequest] = None):
    """
    Creates a new conversation with an empty name in PostgreSQL.
    """
    custom_id = payload.custom_id if payload else None
    conv = await create_conversation(custom_id)
    return conv


@router.get("", response_model=List[ConversationListItem])
async def get_all_conversations():
    """
    Lists all saved conversations for the frontend chats panel.
    Returns only ID and name (content is queried only when clicking a specific chat).
    """
    return await list_conversations(limit=50)


@router.get("/{conv_id}", response_model=ConversationDetail)
async def get_single_conversation(conv_id: str):
    """
    Retrieves full message history for a conversation from PostgreSQL.
    """
    conv = await get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.post("/{conv_id}/messages")
async def save_message_exchange(conv_id: str, payload: AppendExchangeRequest):
    """
    Appends a completed user + assistant exchange into PostgreSQL.
    """
    new_messages = [
        {"role": "user", "content": payload.user_message},
        {"role": "assistant", "content": payload.assistant_response}
    ]
    success = await append_messages_to_conversation(conv_id, new_messages)
    return {"status": "success" if success else "failed"}


@router.post("/{conv_id}/generate-title", response_model=GenerateTitleResponse)
async def generate_title_for_conversation(conv_id: str, payload: GenerateTitleRequest):
    """
    Mini-agent that generates a 2-3 word title based on the first exchange
    using stream=False, thinking=False, and NO tool schemas/calls.
    Updates PostgreSQL with the generated title.
    """
    # 1. Format clean exchange (user prompt, agent reasoning, final response)
    formatted_exchange = parse_exchange_for_titling(payload.user_message, payload.assistant_response)

    # 2. ModelRequest with NO tool schemas, stream=False, thinking=False
    req = ModelRequest(
        user_content=formatted_exchange,
        system_content=CONVERSATION_NAMING_SYSTEM_PROMPT,
        model="default",
        temperature=0.2,
        stream=False,
        thinking=False,
        tools=None,
        tool_choice=None
    )

    clean_title = "New Chat"
    try:
        response = await send_async_chat_request(req)
        if response and response.choices:
            raw_text = response.choices[0].message.content or ""
            # Strip markdown formatting, quotes, and newlines
            candidate = re.sub(r'[*_`"\'#]', '', raw_text).replace('\n', ' ').strip()
            # Strip leading "Title:" or "Topic:" prefixes
            candidate = re.sub(r'^(title|conversation title|topic)\s*:\s*', '', candidate, flags=re.IGNORECASE).strip()
            # Strip trailing punctuation
            candidate = candidate.rstrip('.,:;!-?')
            words = candidate.split()
            if len(words) >= 2:
                clean_title = " ".join(words[:3]).title()
            elif len(words) == 1:
                clean_title = f"{words[0].title()} Overview"
            else:
                words = payload.user_message.strip().split()
                clean_title = " ".join(words[:3]).title() if words else "New Chat"
    except Exception as e:
        logger.warning(f"Error calling model for title generation: {e}")
        words = payload.user_message.strip().split()
        clean_title = " ".join(words[:3]).title() if words else "New Chat"

    # 3. Save generated title into PostgreSQL
    await update_conversation_name(conv_id, clean_title)

    return GenerateTitleResponse(conversation_id=conv_id, title=clean_title)


@router.delete("/{conv_id}")
async def remove_conversation(conv_id: str):
    """
    Deletes a conversation from PostgreSQL.
    """
    success = await delete_conversation(conv_id)
    return {"status": "success" if success else "failed"}

