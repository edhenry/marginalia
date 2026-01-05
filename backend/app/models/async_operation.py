"""Async operation models for background tasks."""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OperationType(str, enum.Enum):
    """Type of async operation."""

    PAPER_REVIEW = "paper_review"
    PATTERN_ANALYSIS = "pattern_analysis"
    BRIEFING_GENERATION = "briefing_generation"
    SYNTHESIS_DRAFT = "synthesis_draft"


class OperationStatus(str, enum.Enum):
    """Status of an async operation."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AsyncOperation(Base):
    """A background async operation."""

    __tablename__ = "async_operations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[OperationType] = mapped_column(Enum(OperationType), nullable=False)
    status: Mapped[OperationStatus] = mapped_column(
        Enum(OperationStatus), default=OperationStatus.QUEUED, nullable=False
    )
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
