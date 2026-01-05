"""Sync service API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.sync_service import SyncService
from app.services.paper_service import PaperService
from app.schemas.paper import PaperCreate

router = APIRouter(prefix="/sync", tags=["sync"])

# Dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ArxivImportRequest(BaseModel):
    """Request to import a paper from arXiv."""

    arxiv_id: str


class NoteSaveRequest(BaseModel):
    """Request to save a note to Obsidian."""

    title: str
    content: str
    folder: str | None = None


# Notion sync
@router.post("/notion/paper/{paper_id}")
async def sync_paper_to_notion(session: SessionDep, paper_id: str):
    """Sync a paper to Notion."""
    service = SyncService(session)
    result = await service.sync_paper_to_notion(paper_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/notion/pull")
async def sync_from_notion(session: SessionDep):
    """Pull updates from Notion."""
    service = SyncService(session)
    result = await service.sync_notion_to_queue()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# Obsidian sync
@router.post("/obsidian/note")
async def save_note_to_obsidian(
    session: SessionDep,
    request: NoteSaveRequest,
):
    """Save a note to Obsidian inbox."""
    service = SyncService(session)
    result = await service.write_draft_note(
        title=request.title,
        content=request.content,
        folder=request.folder,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/obsidian/literature-note/{paper_id}")
async def generate_literature_note(session: SessionDep, paper_id: str):
    """Generate and save a literature note for a paper."""
    paper_service = PaperService(session)
    sync_service = SyncService(session)

    paper = await paper_service.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Generate note content
    content = await sync_service.generate_literature_note(paper)

    # Save to Obsidian
    result = await sync_service.write_draft_note(
        title=paper.title,
        content=content,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/obsidian/concepts")
async def get_concept_notes(session: SessionDep):
    """Get list of concept notes from Obsidian vault."""
    service = SyncService(session)
    notes = await service.index_concept_notes()
    return {"notes": notes}


# arXiv integration
@router.post("/arxiv/import")
async def import_from_arxiv(
    session: SessionDep,
    request: ArxivImportRequest,
):
    """Import a paper from arXiv."""
    sync_service = SyncService(session)
    paper_service = PaperService(session)

    # Fetch paper data from arXiv
    result = await sync_service.import_from_arxiv(request.arxiv_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    paper_data = result["paper_data"]

    # Create paper in system
    paper = await paper_service.create_paper(
        PaperCreate(
            title=paper_data["title"],
            authors=paper_data["authors"],
            abstract=paper_data.get("abstract"),
            source_id=paper_data["source_id"],
            source_url=paper_data["source_url"],
        )
    )

    # Fetch PDF
    pdf_result = await sync_service.fetch_pdf_from_url(
        paper_data["pdf_url"],
        paper.id,
    )

    return {
        "success": True,
        "paper_id": paper.id,
        "title": paper.title,
        "pdf_fetched": "error" not in pdf_result,
    }
