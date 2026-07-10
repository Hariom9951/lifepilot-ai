"""Assistant Pydantic schemas for requests and responses."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatAction(BaseModel):
    """Represents a structured action item that the user can execute from the chat."""

    type: str = Field(
        ..., description="Action type: 'task', 'goal', 'habit', 'expense'"
    )
    label: str = Field(..., description="Short user-friendly action description")
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Metadata payload"
    )


class ChatRequest(BaseModel):
    """Request payload for POST /api/v1/assistant/chat."""

    message: str = Field(..., min_length=1, description="The user query text")
    conversation_id: uuid.UUID | None = Field(
        None, description="Optional UUID to continue an existing chat thread"
    )


class ChatResponse(BaseModel):
    """Response payload returned by the assistant chat endpoint."""

    response: str = Field(..., description="The markdown assistant response text")
    recommendations: list[str] = Field(
        default_factory=list, description="Suggestions or key indicators"
    )
    actions: list[ChatAction] = Field(
        default_factory=list, description="Interactive action items"
    )
    conversation_id: uuid.UUID = Field(
        ..., description="The session ID associated with this chat thread"
    )


class ChatHistoryItem(BaseModel):
    """A single persisted exchange in the chat history list."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    user_message: str
    assistant_message: str
    recommendations: list[str]
    actions: list[ChatAction]
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Response containing conversation history list grouped or paginated."""

    items: list[ChatHistoryItem] = Field(default_factory=list)
