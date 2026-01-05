"""Research context API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
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
from app.services.research_context_service import ResearchContextService
from app.services.claude_service import ClaudeService

router = APIRouter(prefix="/context", tags=["context"])

# Dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Default user ID for MVP (single-user system)
DEFAULT_USER_ID = "default_user"


@router.get("", response_model=ResearchContextResponse)
async def get_context(session: SessionDep):
    """Get full research context."""
    service = ResearchContextService(session)
    context = await service.get_or_create_context(DEFAULT_USER_ID)
    return context


@router.get("/summary")
async def get_context_summary(session: SessionDep):
    """Get condensed context summary for display."""
    service = ResearchContextService(session)
    summary = await service.get_context_summary(DEFAULT_USER_ID)
    return {"summary": summary}


# Research Questions
@router.get("/questions", response_model=list[ResearchQuestionResponse])
async def get_research_questions(session: SessionDep):
    """Get all research questions."""
    service = ResearchContextService(session)
    questions = await service.get_research_questions(DEFAULT_USER_ID)
    return questions


@router.post("/questions", response_model=ResearchQuestionResponse)
async def create_research_question(
    session: SessionDep,
    question_data: ResearchQuestionCreate,
):
    """Create a new research question."""
    service = ResearchContextService(session)
    question = await service.create_research_question(DEFAULT_USER_ID, question_data)
    return question


@router.patch("/questions/{question_id}", response_model=ResearchQuestionResponse)
async def update_research_question(
    session: SessionDep,
    question_id: str,
    question_data: ResearchQuestionUpdate,
):
    """Update a research question."""
    service = ResearchContextService(session)
    question = await service.update_research_question(question_id, question_data)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.delete("/questions/{question_id}")
async def delete_research_question(session: SessionDep, question_id: str):
    """Delete a research question."""
    service = ResearchContextService(session)
    success = await service.delete_research_question(question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"success": True}


# Reading Events
@router.post("/events")
async def record_reading_event(
    session: SessionDep,
    event_data: ReadingEventCreate,
):
    """Record a reading event."""
    service = ResearchContextService(session)
    event = await service.record_reading_event(DEFAULT_USER_ID, event_data)
    return {"success": True, "event_id": event.id}


@router.get("/events")
async def get_reading_history(
    session: SessionDep,
    limit: int = 100,
):
    """Get reading history."""
    service = ResearchContextService(session)
    events = await service.get_reading_history(DEFAULT_USER_ID, limit)
    return events


# Patterns
@router.get("/patterns", response_model=list[PatternResponse])
async def get_patterns(session: SessionDep):
    """Get identified patterns."""
    service = ResearchContextService(session)
    patterns = await service.get_patterns(DEFAULT_USER_ID)
    return patterns


@router.post("/patterns/{pattern_id}/acknowledge", response_model=PatternResponse)
async def acknowledge_pattern(session: SessionDep, pattern_id: str):
    """Mark a pattern as acknowledged."""
    service = ResearchContextService(session)
    pattern = await service.acknowledge_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pattern


@router.post("/analyze")
async def trigger_pattern_analysis(session: SessionDep):
    """Trigger pattern analysis."""
    claude_service = ClaudeService(session)
    operation = await claude_service.queue_pattern_analysis(DEFAULT_USER_ID)
    return {"success": True, "operation_id": operation.id}


# Preferences
@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(session: SessionDep):
    """Get user preferences."""
    service = ResearchContextService(session)
    prefs = await service.get_preferences(DEFAULT_USER_ID)
    return prefs


@router.patch("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    session: SessionDep,
    prefs_data: UserPreferencesUpdate,
):
    """Update user preferences."""
    service = ResearchContextService(session)
    prefs = await service.update_preferences(DEFAULT_USER_ID, prefs_data)
    return prefs


# Briefings
@router.post("/briefing")
async def generate_briefing(session: SessionDep):
    """Generate a research briefing."""
    claude_service = ClaudeService(session)
    briefing = await claude_service.generate_briefing(DEFAULT_USER_ID)
    return briefing
