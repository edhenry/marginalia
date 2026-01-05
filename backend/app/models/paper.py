"""Paper-related database models."""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PaperStatus(str, enum.Enum):
    """Status of a paper in the reading workflow."""

    NEW = "new"  # Just added, not yet processed
    PROCESSING = "processing"  # Claude is reviewing
    CLAUDE_REVIEWED = "claude_reviewed"  # Ready for human
    READING = "reading"  # Human is actively reading
    READ = "read"  # Human finished reading
    SYNTHESIZED = "synthesized"  # Literature note complete
    ARCHIVED = "archived"  # No longer active


class Paper(Base):
    """A research paper in the system."""

    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[list[str]] = mapped_column(JSON, default=list)
    venue: Mapped[str | None] = mapped_column(String(200), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)

    # URLs and storage
    pdf_url: Mapped[str] = mapped_column(String(500), nullable=False)  # Internal blob storage URL
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # arXiv ID, DOI

    # Workflow metadata
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[PaperStatus] = mapped_column(
        Enum(PaperStatus), default=PaperStatus.NEW, nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=50)  # 0-100, higher = more priority
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1
    relevance_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Categorization
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Claude's review
    claude_review: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # External integrations
    notion_page_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    annotations: Mapped[list["Annotation"]] = relationship(
        "Annotation", back_populates="paper", cascade="all, delete-orphan"
    )
    connections: Mapped[list["PaperConnection"]] = relationship(
        "PaperConnection",
        back_populates="source_paper",
        foreign_keys="PaperConnection.source_paper_id",
        cascade="all, delete-orphan",
    )


class PaperConnection(Base):
    """A connection between two papers."""

    __tablename__ = "paper_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_paper_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("papers.id"), nullable=False
    )
    target_paper_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("papers.id"), nullable=True
    )
    target_title: Mapped[str] = mapped_column(String(500), nullable=False)
    connection_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # cites, cited_by, similar, foundational, contrasts
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    source_paper: Mapped["Paper"] = relationship(
        "Paper", back_populates="connections", foreign_keys=[source_paper_id]
    )


class AnnotationPosition(Base):
    """Position of an annotation on a PDF page."""

    __tablename__ = "annotation_positions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    annotation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("annotations.id"), nullable=False
    )
    page_index: Mapped[int] = mapped_column(Integer, nullable=False)
    rects: Mapped[list[dict[str, float]]] = mapped_column(
        JSON, default=list
    )  # [{x, y, width, height}]

    # Relationship
    annotation: Mapped["Annotation"] = relationship("Annotation", back_populates="position")


class Annotation(Base):
    """An annotation on a paper (highlight, note, or question)."""

    __tablename__ = "annotations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_id: Mapped[str] = mapped_column(String(36), ForeignKey("papers.id"), nullable=False)
    author: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" or "claude"
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # highlight, note, question
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Note or question text
    thread_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="annotations")
    position: Mapped["AnnotationPosition"] = relationship(
        "AnnotationPosition",
        back_populates="annotation",
        uselist=False,
        cascade="all, delete-orphan",
    )
