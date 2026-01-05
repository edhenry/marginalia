"""Research context models for tracking user's research agenda and patterns."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResearchContext(Base):
    """Top-level research context for a user."""

    __tablename__ = "research_contexts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    research_questions: Mapped[list["ResearchQuestion"]] = relationship(
        "ResearchQuestion", back_populates="context", cascade="all, delete-orphan"
    )
    reading_events: Mapped[list["ReadingEvent"]] = relationship(
        "ReadingEvent", back_populates="context", cascade="all, delete-orphan"
    )
    patterns: Mapped[list["Pattern"]] = relationship(
        "Pattern", back_populates="context", cascade="all, delete-orphan"
    )
    preferences: Mapped["UserPreferences"] = relationship(
        "UserPreferences",
        back_populates="context",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ResearchQuestion(Base):
    """An active research question the user is exploring."""

    __tablename__ = "research_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    context_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_contexts.id"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, paused, resolved
    related_paper_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    context: Mapped["ResearchContext"] = relationship(
        "ResearchContext", back_populates="research_questions"
    )


class ReadingEvent(Base):
    """A reading event for tracking user's reading activity."""

    __tablename__ = "reading_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    context_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_contexts.id"), nullable=False
    )
    paper_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # started, annotated, discussed, completed, synthesized
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    context: Mapped["ResearchContext"] = relationship(
        "ResearchContext", back_populates="reading_events"
    )


class Pattern(Base):
    """A pattern identified by Claude across the user's reading."""

    __tablename__ = "patterns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    context_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_contexts.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    paper_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    identified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    context: Mapped["ResearchContext"] = relationship(
        "ResearchContext", back_populates="patterns"
    )


class UserPreferences(Base):
    """User preferences for the system."""

    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    context_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_contexts.id"), unique=True, nullable=False
    )

    # Prioritization weights (0-1)
    weight_relevance: Mapped[float] = mapped_column(default=0.4)
    weight_recency: Mapped[float] = mapped_column(default=0.2)
    weight_foundational: Mapped[float] = mapped_column(default=0.3)
    weight_social: Mapped[float] = mapped_column(default=0.1)

    # Notification preferences
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    email_digest: Mapped[str] = mapped_column(String(20), default="none")  # none, daily, weekly

    # Briefing schedule (cron expression)
    briefing_schedule: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Quiet hours
    quiet_hours_start: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quiet_hours_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quiet_hours_timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    context: Mapped["ResearchContext"] = relationship(
        "ResearchContext", back_populates="preferences"
    )
