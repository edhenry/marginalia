"""API routes module."""

from app.api.routes.papers import router as papers_router
from app.api.routes.context import router as context_router
from app.api.routes.chat import router as chat_router
from app.api.routes.sync import router as sync_router

__all__ = ["papers_router", "context_router", "chat_router", "sync_router"]
