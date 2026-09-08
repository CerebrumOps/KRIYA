# ==============================================================================
# KRIYA Backend Schema: Conversations API
# ==============================================================================
# Pydantic request & response schemas for conversation management and title generation.
# ==============================================================================

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    custom_id: Optional[str] = Field(None, description="Optional custom ID for the conversation")


class ConversationListItem(BaseModel):
    id: str = Field(..., description="Unique conversation identifier")
    name: str = Field("New Chat", description="Title of the conversation for chats panel")


class ConversationSummary(ConversationListItem):
    """Backwards-compatible alias for ConversationListItem."""
    pass



class ConversationDetail(BaseModel):
    id: str
    name: str = Field("New Chat", description="Title of the conversation")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="All message exchanges")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AppendExchangeRequest(BaseModel):
    user_message: str = Field(..., description="User's input prompt")
    assistant_response: str = Field(..., description="Assistant's full reply including thoughts/tools")


class GenerateTitleRequest(BaseModel):
    user_message: str = Field(..., description="The first user query")
    assistant_response: str = Field(..., description="The first assistant response")


class GenerateTitleResponse(BaseModel):
    conversation_id: str
    title: str = Field(..., description="2-3 word generated conversation title")
