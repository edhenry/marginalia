"""Pydantic schemas for Research Context API operations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResearchQuestionCreate(BaseModel):
    """Schema for creating a research question."""

    question: str
    description: str | None = None
    related_paper_ids: list[str] = Field(default_factory=list)


class ResearchQuestionUpdate(BaseModel):
    """Schema for updating a research question."""

    question: str | None = None
    description: str | None = None
    status: str | None = None  # active, paused, resolved
    related_paper_ids: list[str] | None = None


class ResearchQuestionResponse(BaseModel):
    """Schema for research question response."""

    id: str
    question: str
    description: str | None
    status: str
    related_paper_ids: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReadingEventCreate(BaseModel):
    """Schema for creating a reading event."""

    paper_id: str
    action: str  # started, annotated, discussed, completed, synthesized
    metadata: dict[str, Any] | None = None


class PatternResponse(BaseModel):
    """Schema for pattern response."""

    id: str
    description: str
    paper_ids: list[str]
    identified_at: datetime
    acknowledged: bool

    class Config:
        from_attributes = True


class UserPreferencesResponse(BaseModel):
    """Schema for user preferences response."""

    weight_relevance: float
    weight_recency: float
    weight_foundational: float
    weight_social: float
    push_enabled: bool
    email_enabled: bool
    email_digest: str
    briefing_schedule: str | None
    quiet_hours_start: str | None
    quiet_hours_end: str | None
    quiet_hours_timezone: str | None

    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""

    weight_relevance: float | None = None
    weight_recency: float | None = None
    weight_foundational: float | None = None
    weight_social: float | None = None
    push_enabled: bool | None = None
    email_enabled: bool | None = None
    email_digest: str | None = None
    briefing_schedule: str | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    quiet_hours_timezone: str | None = None


class ResearchContextResponse(BaseModel):
    """Schema for full research context response."""

    id: str
    user_id: str
    research_questions: list[ResearchQuestionResponse]
    patterns: list[PatternResponse]
    preferences: UserPreferencesResponse | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
