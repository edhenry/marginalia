"""Chat API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.chat import ChatMessage, ChatThread
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatThreadCreate,
    ChatThreadResponse,
)
from app.services.claude_service import ClaudeService

router = APIRouter(prefix="/chat", tags=["chat"])

# Dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Default user ID for MVP
DEFAULT_USER_ID = "default_user"


def _thread_to_response(thread: ChatThread, messages: list[ChatMessage] = None) -> ChatThreadResponse:
    """Convert a ChatThread model to response schema."""
    return ChatThreadResponse(
        id=thread.id,
        context_type=thread.context_type,
        paper_id=thread.paper_id,
        question_id=thread.question_id,
        synthesis_scope=thread.synthesis_scope,
        messages=[
            ChatMessageResponse(
                id=m.id,
                thread_id=m.thread_id,
                role=m.role,
                content=m.content,
                annotation_references=m.annotation_references,
                created_at=m.created_at,
            )
            for m in (messages or thread.messages or [])
        ],
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


@router.post("/threads", response_model=ChatThreadResponse)
async def create_thread(
    session: SessionDep,
    thread_data: ChatThreadCreate,
):
    """Create a new chat thread."""
    claude_service = ClaudeService(session)
    thread = await claude_service.create_thread(
        context_type=thread_data.context_type,
        paper_id=thread_data.paper_id,
        question_id=thread_data.question_id,
        synthesis_scope=thread_data.synthesis_scope,
    )
    return _thread_to_response(thread, [])


@router.get("/threads/{thread_id}", response_model=ChatThreadResponse)
async def get_thread(session: SessionDep, thread_id: str):
    """Get a chat thread with messages."""
    result = await session.execute(
        select(ChatThread)
        .options(selectinload(ChatThread.messages))
        .where(ChatThread.id == thread_id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return _thread_to_response(thread)


@router.get("/threads", response_model=list[ChatThreadResponse])
async def list_threads(
    session: SessionDep,
    paper_id: str | None = None,
    question_id: str | None = None,
    limit: int = 20,
):
    """List chat threads with optional filters."""
    query = select(ChatThread).options(selectinload(ChatThread.messages))

    if paper_id:
        query = query.where(ChatThread.paper_id == paper_id)
    if question_id:
        query = query.where(ChatThread.question_id == question_id)

    query = query.order_by(ChatThread.updated_at.desc()).limit(limit)
    result = await session.execute(query)
    threads = list(result.scalars().all())
    return [_thread_to_response(t) for t in threads]


@router.post("/threads/{thread_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session: SessionDep,
    thread_id: str,
    message_data: ChatMessageCreate,
):
    """Send a message in a chat thread and get Claude's response."""
    claude_service = ClaudeService(session)

    # Verify thread exists
    result = await session.execute(
        select(ChatThread).where(ChatThread.id == thread_id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Get Claude's response
    response = await claude_service.chat(
        thread_id=thread_id,
        message=message_data.content,
        user_id=DEFAULT_USER_ID,
    )

    return ChatMessageResponse(
        id=response.id,
        thread_id=response.thread_id,
        role=response.role,
        content=response.content,
        annotation_references=response.annotation_references,
        created_at=response.created_at,
    )


@router.get("/threads/{thread_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    session: SessionDep,
    thread_id: str,
    limit: int = 50,
    offset: int = 0,
):
    """Get messages in a chat thread."""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at)
        .offset(offset)
        .limit(limit)
    )
    messages = list(result.scalars().all())
    return [
        ChatMessageResponse(
            id=m.id,
            thread_id=m.thread_id,
            role=m.role,
            content=m.content,
            annotation_references=m.annotation_references,
            created_at=m.created_at,
        )
        for m in messages
    ]
