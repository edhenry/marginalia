"""Service layer for research context operations."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.research_context import (
    Pattern,
    ReadingEvent,
    ResearchContext,
    ResearchQuestion,
    UserPreferences,
)
from app.schemas.research_context import (
    ReadingEventCreate,
    ResearchQuestionCreate,
    ResearchQuestionUpdate,
    UserPreferencesUpdate,
)


class ResearchContextService:
    """Service for managing research context."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_context(self, user_id: str) -> ResearchContext:
        """Get or create a research context for a user."""
        result = await self.session.execute(
            select(ResearchContext)
            .options(
                selectinload(ResearchContext.research_questions),
                selectinload(ResearchContext.patterns),
                selectinload(ResearchContext.preferences),
            )
            .where(ResearchContext.user_id == user_id)
        )
        context = result.scalar_one_or_none()

        if not context:
            context = ResearchContext(
                id=str(uuid.uuid4()),
                user_id=user_id,
            )
            self.session.add(context)

            # Create default preferences
            preferences = UserPreferences(
                id=str(uuid.uuid4()),
                context_id=context.id,
            )
            self.session.add(preferences)

            await self.session.flush()

            # Reload with relationships
            result = await self.session.execute(
                select(ResearchContext)
                .options(
                    selectinload(ResearchContext.research_questions),
                    selectinload(ResearchContext.patterns),
                    selectinload(ResearchContext.preferences),
                )
                .where(ResearchContext.id == context.id)
            )
            context = result.scalar_one()

        return context

    # Research Questions
    async def create_research_question(
        self, user_id: str, question_data: ResearchQuestionCreate
    ) -> ResearchQuestion:
        """Create a research question."""
        context = await self.get_or_create_context(user_id)

        question = ResearchQuestion(
            id=str(uuid.uuid4()),
            context_id=context.id,
            question=question_data.question,
            description=question_data.description,
            related_paper_ids=question_data.related_paper_ids,
        )
        self.session.add(question)
        await self.session.flush()
        return question

    async def get_research_questions(self, user_id: str) -> list[ResearchQuestion]:
        """Get all research questions for a user."""
        context = await self.get_or_create_context(user_id)
        return context.research_questions

    async def update_research_question(
        self, question_id: str, question_data: ResearchQuestionUpdate
    ) -> ResearchQuestion | None:
        """Update a research question."""
        result = await self.session.execute(
            select(ResearchQuestion).where(ResearchQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            return None

        update_data = question_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)

        question.updated_at = datetime.utcnow()
        await self.session.flush()
        return question

    async def delete_research_question(self, question_id: str) -> bool:
        """Delete a research question."""
        result = await self.session.execute(
            select(ResearchQuestion).where(ResearchQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            return False

        await self.session.delete(question)
        await self.session.flush()
        return True

    # Reading Events
    async def record_reading_event(
        self, user_id: str, event_data: ReadingEventCreate
    ) -> ReadingEvent:
        """Record a reading event."""
        context = await self.get_or_create_context(user_id)

        event = ReadingEvent(
            id=str(uuid.uuid4()),
            context_id=context.id,
            paper_id=event_data.paper_id,
            action=event_data.action,
            metadata=event_data.metadata,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_reading_history(
        self, user_id: str, limit: int = 100
    ) -> list[ReadingEvent]:
        """Get reading history for a user."""
        context = await self.get_or_create_context(user_id)

        result = await self.session.execute(
            select(ReadingEvent)
            .where(ReadingEvent.context_id == context.id)
            .order_by(ReadingEvent.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # Patterns
    async def get_patterns(self, user_id: str) -> list[Pattern]:
        """Get identified patterns for a user."""
        context = await self.get_or_create_context(user_id)
        return context.patterns

    async def acknowledge_pattern(self, pattern_id: str) -> Pattern | None:
        """Mark a pattern as acknowledged."""
        result = await self.session.execute(
            select(Pattern).where(Pattern.id == pattern_id)
        )
        pattern = result.scalar_one_or_none()
        if not pattern:
            return None

        pattern.acknowledged = True
        await self.session.flush()
        return pattern

    async def create_pattern(
        self, user_id: str, description: str, paper_ids: list[str]
    ) -> Pattern:
        """Create a new pattern (typically called by Claude service)."""
        context = await self.get_or_create_context(user_id)

        pattern = Pattern(
            id=str(uuid.uuid4()),
            context_id=context.id,
            description=description,
            paper_ids=paper_ids,
        )
        self.session.add(pattern)
        await self.session.flush()
        return pattern

    # Preferences
    async def get_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences."""
        context = await self.get_or_create_context(user_id)
        return context.preferences

    async def update_preferences(
        self, user_id: str, prefs_data: UserPreferencesUpdate
    ) -> UserPreferences:
        """Update user preferences."""
        context = await self.get_or_create_context(user_id)
        prefs = context.preferences

        update_data = prefs_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prefs, field, value)

        await self.session.flush()
        return prefs

    async def get_context_summary(self, user_id: str) -> str:
        """Get a condensed context summary for Claude prompts."""
        context = await self.get_or_create_context(user_id)

        # Build summary
        lines = []

        # Active research questions
        active_questions = [q for q in context.research_questions if q.status == "active"]
        if active_questions:
            lines.append("Active Research Questions:")
            for q in active_questions:
                lines.append(f"- {q.question}")
                if q.description:
                    lines.append(f"  {q.description}")

        # Recent patterns
        unacknowledged_patterns = [p for p in context.patterns if not p.acknowledged]
        if unacknowledged_patterns:
            lines.append("\nRecent Patterns Identified:")
            for p in unacknowledged_patterns[:3]:
                lines.append(f"- {p.description}")

        return "\n".join(lines) if lines else "No research context established yet."
