"""Chat and discussion thread models."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ChatThread(Base):
    """A chat thread for discussions about papers or research."""

    __tablename__ = "chat_threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    context_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # paper, research_question, synthesis, general
    paper_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    question_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    synthesis_scope: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # Paper IDs
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="thread", cascade="all, delete-orphan"
    )


class ChatContext(Base):
    """Additional context stored for a chat thread."""

    __tablename__ = "chat_contexts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    thread_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_threads.id"), nullable=False
    )
    context_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """A message in a chat thread."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    thread_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_threads.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    annotation_references: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )  # Links to annotation IDs
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    thread: Mapped["ChatThread"] = relationship("ChatThread", back_populates="messages")
