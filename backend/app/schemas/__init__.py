"""Pydantic schemas for API request/response validation."""

from app.schemas.paper import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
    ClaudeReviewResponse,
    PaperConnection as PaperConnectionSchema,
    PaperCreate,
    PaperResponse,
    PaperUpdate,
    QueueResponse,
)
from app.schemas.research_context import (
    PatternResponse,
    ReadingEventCreate,
    ResearchContextResponse,
    ResearchQuestionCreate,
    ResearchQuestionResponse,
    ResearchQuestionUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatThreadCreate,
    ChatThreadResponse,
)

__all__ = [
    "PaperCreate",
    "PaperUpdate",
    "PaperResponse",
    "PaperConnectionSchema",
    "AnnotationCreate",
    "AnnotationUpdate",
    "AnnotationResponse",
    "ClaudeReviewResponse",
    "QueueResponse",
    "ResearchContextResponse",
    "ResearchQuestionCreate",
    "ResearchQuestionUpdate",
    "ResearchQuestionResponse",
    "ReadingEventCreate",
    "PatternResponse",
    "UserPreferencesResponse",
    "UserPreferencesUpdate",
    "ChatThreadCreate",
    "ChatThreadResponse",
    "ChatMessageCreate",
    "ChatMessageResponse",
]
