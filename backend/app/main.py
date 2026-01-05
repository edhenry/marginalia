"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import papers_router, context_router, chat_router, sync_router
from app.core.config import settings
from app.core.database import init_db
from app.services.task_worker import task_worker, setup_task_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Marginalia...")
    await init_db()

    # Set up and start background task worker
    await setup_task_handlers()
    await task_worker.start()
    logger.info("Background task worker started")

    # Ensure storage directories exist
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    settings.pdf_storage_path.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    logger.info("Shutting down Marginalia...")
    await task_worker.stop()


app = FastAPI(
    title=settings.app_name,
    description="Research Collaboration System - Claude as an active research partner",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(papers_router, prefix=settings.api_v1_prefix)
app.include_router(context_router, prefix=settings.api_v1_prefix)
app.include_router(chat_router, prefix=settings.api_v1_prefix)
app.include_router(sync_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "description": "Research Collaboration System",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
