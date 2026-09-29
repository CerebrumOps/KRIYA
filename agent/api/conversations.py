# ==============================================================================
# KRIYA API: Conversation Management & Automated Title Generation
# ==============================================================================
# Endpoints:
#   - POST /api/conversations
#   - GET /api/conversations
#   - GET /api/conversations/{conv_id}
#   - POST /api/conversations/{conv_id}/messages
#   - POST /api/conversations/{conv_id}/generate-title
#   - DELETE /api/conversations/{conv_id}
#
# Rule: Each endpoint method is followed immediately by its request/response schemas.
# ==============================================================================

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from agent.api.session import get_optional_session
from agent.database.conversation_db.conversation_db import (
    create_conversation,
    get_conversation,
    list_conversations,
    append_messages_to_conversation,
    update_conversation_name,
    delete_conversation,
)
from agent.orchestration.model_client import ModelRequest, send_async_chat_request
from agent.prompts.conversation_naming import CONVERSATION_NAMING_SYSTEM_PROMPT

logger = logging.getLogger("kriya.api.conversations")
router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


def parse_exchange_for_titling(user_message: str, assistant_response: str) -> str:
    """
    Extracts user prompt and clean reasoning/final text to feed the titling agent.
    """
    # Extract reasoning tokens inside <think> tags if any
    think_matches = re.findall(r'<think>([\s\S]*?)</think>', assistant_response)
    extracted_reasoning = " ".join([m.strip() for m in think_matches if m.strip()])

    # Strip tool calls, XML tags, and metadata
    clean_response = re.sub(r'<think>[\s\S]*?</think>', '', assistant_response)
    clean_response = re.sub(r'<tool_call[\s\S]*?</tool_call>', '', clean_response)
    clean_response = re.sub(r'<tool_result[\s\S]*?</tool_result>', '', clean_response)
    clean_response = re.sub(r'<response_metadata>[\s\S]*?</response_metadata>', '', clean_response)
    clean_response = re.sub(r'\s+', ' ', clean_response).strip()

    truncated_reasoning = extracted_reasoning[:1200] if extracted_reasoning else ""
    truncated_response = clean_response[:1200] if clean_response else ""

    parts = [f"User Message:\n{user_message.strip()}"]
    if truncated_reasoning:
        parts.append(f"Agent Reasoning Summary:\n{truncated_reasoning}")
    if truncated_response:
        parts.append(f"Assistant Response:\n{truncated_response}")

    return "\n\n".join(parts)


# ==============================================================================
# 1. CREATE NEW CONVERSATION
# ==============================================================================

@router.post("")
async def create_new_conversation(
    payload: Optional[CreateConversationRequest] = None,
    session: Optional[Dict[str, Any]] = Depends(get_optional_session)
):
    """Creates a new conversation record in PostgreSQL associated with the current user."""
    custom_id = payload.custom_id if payload else None
    employee_id = session.get("employee_id") if session else None
    return await create_conversation(custom_id, employee_id=employee_id)


class CreateConversationRequest(BaseModel):
    custom_id: Optional[str] = Field(None, description="Optional custom ID for the conversation")


class ConversationDetail(BaseModel):
    id: str
    name: str = Field("New Chat", description="Title of the conversation")
    employee_id: Optional[str] = Field(None, description="Owner employee ID")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="All message exchanges")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==============================================================================
# 2. LIST ALL CONVERSATIONS
# ==============================================================================

@router.get("")
async def get_all_conversations(
    session: Optional[Dict[str, Any]] = Depends(get_optional_session)
):
    """Lists saved conversations for the active user's chats panel."""
    employee_id = session.get("employee_id") if session else None
    return await list_conversations(employee_id=employee_id, limit=50)


class ConversationListItem(BaseModel):
    id: str = Field(..., description="Unique conversation identifier")
    name: str = Field("New Chat", description="Title of the conversation for chats panel")


# ==============================================================================
# 3. GET SINGLE CONVERSATION
# ==============================================================================

@router.get("/{conv_id}")
async def get_single_conversation(
    conv_id: str,
    session: Optional[Dict[str, Any]] = Depends(get_optional_session)
):
    """Retrieves full message history for a conversation from PostgreSQL."""
    employee_id = session.get("employee_id") if session else None
    conv = await get_conversation(conv_id, employee_id=employee_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


# ==============================================================================
# 4. APPEND MESSAGE EXCHANGE
# ==============================================================================

@router.post("/{conv_id}/messages")
async def save_message_exchange(
    conv_id: str,
    payload: AppendExchangeRequest,
    session: Optional[Dict[str, Any]] = Depends(get_optional_session)
):
    """Appends a completed user + assistant exchange into PostgreSQL."""
    new_messages = [
        {"role": "user", "content": payload.user_message},
        {"role": "assistant", "content": payload.assistant_response}
    ]
    employee_id = session.get("employee_id") if session else None
    success = await append_messages_to_conversation(conv_id, new_messages, employee_id=employee_id)
    return {"status": "success" if success else "failed"}


class AppendExchangeRequest(BaseModel):
    user_message: str = Field(..., description="User prompt text")
    assistant_response: str = Field(..., description="Assistant response text")


# ==============================================================================
# 5. GENERATE TITLE FOR CONVERSATION
# ==============================================================================

@router.post("/{conv_id}/generate-title")
async def generate_title_for_conversation(conv_id: str, payload: GenerateTitleRequest):
    """
    Mini-agent that generates a 2-3 word title based on the first exchange
    using stream=False, thinking=False, and NO tool schemas/calls.
    """
    formatted_exchange = parse_exchange_for_titling(payload.user_message, payload.assistant_response)

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
            candidate = re.sub(r'[*_`"\'#]', '', raw_text).replace('\n', ' ').strip()
            candidate = re.sub(r'^(title|conversation title|topic)\s*:\s*', '', candidate, flags=re.IGNORECASE).strip()
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

    await update_conversation_name(conv_id, clean_title)
    return GenerateTitleResponse(conversation_id=conv_id, title=clean_title)


class GenerateTitleRequest(BaseModel):
    user_message: str = Field(..., description="First user query")
    assistant_response: str = Field(..., description="First assistant reply")


class GenerateTitleResponse(BaseModel):
    conversation_id: str = Field(..., description="Target conversation ID")
    title: str = Field(..., description="Synthesized 2-3 word title")


# ==============================================================================
# 6. DELETE CONVERSATION
# ==============================================================================

@router.delete("/{conv_id}")
async def remove_conversation(conv_id: str):
    """Deletes a conversation from PostgreSQL."""
    success = await delete_conversation(conv_id)
    return {"status": "success" if success else "failed"}
