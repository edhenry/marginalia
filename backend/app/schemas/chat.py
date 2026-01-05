"""Pydantic schemas for Chat API operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""

    content: str
    annotation_references: list[str] | None = None


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""

    id: str
    thread_id: str
    role: str
    content: str
    annotation_references: list[str] | None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatThreadCreate(BaseModel):
    """Schema for creating a chat thread."""

    context_type: str  # paper, research_question, synthesis, general
    paper_id: str | None = None
    question_id: str | None = None
    synthesis_scope: list[str] | None = None


class ChatThreadResponse(BaseModel):
    """Schema for chat thread response."""

    id: str
    context_type: str
    paper_id: str | None
    question_id: str | None
    synthesis_scope: list[str] | None
    messages: list[ChatMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
