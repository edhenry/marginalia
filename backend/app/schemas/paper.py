"""Pydantic schemas for Paper-related API operations."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.paper import PaperStatus


class AnnotationPositionSchema(BaseModel):
    """Schema for annotation position on PDF."""

    page_index: int
    rects: list[dict[str, float]] = Field(default_factory=list)


class AnnotationCreate(BaseModel):
    """Schema for creating an annotation."""

    author: str = "user"  # user or claude
    type: str  # highlight, note, question
    page_number: int
    selected_text: str | None = None
    content: str
    position: AnnotationPositionSchema | None = None


class AnnotationUpdate(BaseModel):
    """Schema for updating an annotation."""

    content: str | None = None
    selected_text: str | None = None


class AnnotationResponse(BaseModel):
    """Schema for annotation response."""

    id: str
    paper_id: str
    author: str
    type: str
    page_number: int
    selected_text: str | None
    content: str
    thread_id: str | None
    created_at: datetime
    position: AnnotationPositionSchema | None = None

    class Config:
        from_attributes = True


class PaperConnection(BaseModel):
    """Schema for paper connection."""

    target_paper_id: str | None = None
    target_title: str
    connection_type: str  # cites, cited_by, similar, foundational, contrasts
    explanation: str


class ClaudeReviewResponse(BaseModel):
    """Schema for Claude's paper review."""

    summary: str
    key_contributions: list[str]
    methodology: str | None = None
    relevance_analysis: str
    connections: list[PaperConnection]
    suggested_tags: list[str]
    discussion_questions: list[str]
    reviewed_at: datetime


class PaperCreate(BaseModel):
    """Schema for creating a paper."""

    title: str
    authors: list[str] = Field(default_factory=list)
    venue: str | None = None
    year: int | None = None
    abstract: str | None = None
    source_url: str | None = None
    source_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class PaperUpdate(BaseModel):
    """Schema for updating a paper."""

    title: str | None = None
    authors: list[str] | None = None
    venue: str | None = None
    year: int | None = None
    abstract: str | None = None
    status: PaperStatus | None = None
    priority: int | None = None
    tags: list[str] | None = None


class PaperResponse(BaseModel):
    """Schema for paper response."""

    id: str
    title: str
    authors: list[str]
    venue: str | None
    year: int | None
    abstract: str | None
    pdf_url: str
    source_url: str | None
    source_id: str | None
    added_at: datetime
    status: PaperStatus
    priority: int
    relevance_score: float | None
    relevance_reason: str | None
    tags: list[str]
    claude_review: dict | None
    notion_page_id: str | None
    annotation_count: int = 0

    class Config:
        from_attributes = True


class QueueResponse(BaseModel):
    """Schema for reading queue response."""

    papers: list[PaperResponse]
    total_count: int
    new_count: int
    claude_reviewed_count: int
    reading_count: int
