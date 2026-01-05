"""Paper-related API routes."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.paper import PaperStatus
from app.schemas.paper import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
    PaperCreate,
    PaperResponse,
    PaperUpdate,
    QueueResponse,
)
from app.services.paper_service import PaperService
from app.services.claude_service import ClaudeService

router = APIRouter(prefix="/papers", tags=["papers"])

# Dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _paper_to_response(paper) -> PaperResponse:
    """Convert a Paper model to PaperResponse schema."""
    return PaperResponse(
        id=paper.id,
        title=paper.title,
        authors=paper.authors,
        venue=paper.venue,
        year=paper.year,
        abstract=paper.abstract,
        pdf_url=paper.pdf_url,
        source_url=paper.source_url,
        source_id=paper.source_id,
        added_at=paper.added_at,
        status=paper.status,
        priority=paper.priority,
        relevance_score=paper.relevance_score,
        relevance_reason=paper.relevance_reason,
        tags=paper.tags,
        claude_review=paper.claude_review,
        notion_page_id=paper.notion_page_id,
        annotation_count=len(paper.annotations) if paper.annotations else 0,
    )


@router.post("", response_model=PaperResponse)
async def create_paper(
    session: SessionDep,
    paper_data: PaperCreate,
    trigger_review: bool = Query(True, description="Queue Claude review immediately"),
):
    """Create a new paper from JSON data."""
    service = PaperService(session)

    paper = await service.create_paper(paper_data, None, None)

    # Queue Claude review if requested
    if trigger_review:
        claude_service = ClaudeService(session)
        await claude_service.queue_paper_review(paper.id, "default_user")

    return _paper_to_response(paper)


@router.post("/upload", response_model=PaperResponse)
async def upload_paper(
    session: SessionDep,
    pdf_file: UploadFile = File(...),
    title: str = Form(...),
    authors: str = Form(""),  # JSON array as string
    venue: str | None = Form(None),
    year: int | None = Form(None),
    abstract: str | None = Form(None),
    source_url: str | None = Form(None),
    source_id: str | None = Form(None),
    tags: str = Form(""),  # JSON array as string
    trigger_review: bool = Form(True),
):
    """Upload a paper with PDF file."""
    service = PaperService(session)

    # Parse JSON arrays
    try:
        authors_list = json.loads(authors) if authors else []
    except json.JSONDecodeError:
        authors_list = [a.strip() for a in authors.split(",") if a.strip()]

    try:
        tags_list = json.loads(tags) if tags else []
    except json.JSONDecodeError:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    paper_data = PaperCreate(
        title=title,
        authors=authors_list,
        venue=venue,
        year=year,
        abstract=abstract,
        source_url=source_url,
        source_id=source_id,
        tags=tags_list,
    )

    paper = await service.create_paper(paper_data, pdf_file.file, pdf_file.filename)

    # Queue Claude review if requested
    if trigger_review:
        claude_service = ClaudeService(session)
        await claude_service.queue_paper_review(paper.id, "default_user")

    return _paper_to_response(paper)


@router.post("/{paper_id}/pdf")
async def upload_pdf_for_paper(
    session: SessionDep,
    paper_id: str,
    pdf_file: UploadFile = File(...),
    trigger_review: bool = Query(True),
):
    """Upload or replace PDF for an existing paper."""
    from app.services.sync_service import SyncService

    service = PaperService(session)
    paper = await service.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Store the PDF
    pdf_path = await service._store_pdf(paper_id, pdf_file.file, pdf_file.filename)
    paper.pdf_url = pdf_path
    await session.flush()

    # Queue Claude review if requested
    if trigger_review and paper.status in [PaperStatus.NEW, PaperStatus.PROCESSING]:
        claude_service = ClaudeService(session)
        await claude_service.queue_paper_review(paper.id, "default_user")

    return {"success": True, "pdf_path": pdf_path}


@router.get("", response_model=list[PaperResponse])
async def list_papers(
    session: SessionDep,
    status: PaperStatus | None = None,
    tags: list[str] | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List papers with optional filters."""
    service = PaperService(session)
    papers, total = await service.list_papers(status, tags, limit, offset)
    return [_paper_to_response(p) for p in papers]


@router.get("/queue", response_model=QueueResponse)
async def get_queue(session: SessionDep):
    """Get the prioritized reading queue."""
    service = PaperService(session)
    queue = await service.get_queue()
    return QueueResponse(
        papers=[_paper_to_response(p) for p in queue["papers"]],
        total_count=queue["total_count"],
        new_count=queue["new_count"],
        claude_reviewed_count=queue["claude_reviewed_count"],
        reading_count=queue["reading_count"],
    )


@router.post("/queue/reorder")
async def reorder_queue(
    session: SessionDep,
    paper_ids: list[str],
):
    """Reorder papers in the queue."""
    service = PaperService(session)
    success = await service.reorder_queue(paper_ids)
    return {"success": success}


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(session: SessionDep, paper_id: str):
    """Get a paper by ID."""
    service = PaperService(session)
    paper = await service.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return _paper_to_response(paper)


@router.patch("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    session: SessionDep,
    paper_id: str,
    paper_data: PaperUpdate,
):
    """Update a paper."""
    service = PaperService(session)
    paper = await service.update_paper(paper_id, paper_data)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return _paper_to_response(paper)


@router.delete("/{paper_id}")
async def delete_paper(session: SessionDep, paper_id: str):
    """Archive/delete a paper."""
    service = PaperService(session)
    success = await service.delete_paper(paper_id)
    if not success:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"success": True}


@router.get("/{paper_id}/pdf")
async def get_pdf(session: SessionDep, paper_id: str):
    """Get the PDF content for a paper."""
    service = PaperService(session)
    pdf_path = await service.get_pdf_path(paper_id)
    if not pdf_path or not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_path, media_type="application/pdf")


# Annotation routes
@router.get("/{paper_id}/annotations", response_model=list[AnnotationResponse])
async def get_annotations(session: SessionDep, paper_id: str):
    """Get all annotations for a paper."""
    service = PaperService(session)
    annotations = await service.get_annotations(paper_id)
    return annotations


@router.post("/{paper_id}/annotations", response_model=AnnotationResponse)
async def create_annotation(
    session: SessionDep,
    paper_id: str,
    annotation_data: AnnotationCreate,
):
    """Create an annotation on a paper."""
    service = PaperService(session)
    annotation = await service.create_annotation(paper_id, annotation_data)
    if not annotation:
        raise HTTPException(status_code=404, detail="Paper not found")
    return annotation


@router.patch("/annotations/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    session: SessionDep,
    annotation_id: str,
    annotation_data: AnnotationUpdate,
):
    """Update an annotation."""
    service = PaperService(session)
    annotation = await service.update_annotation(annotation_id, annotation_data)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return annotation


@router.delete("/annotations/{annotation_id}")
async def delete_annotation(session: SessionDep, annotation_id: str):
    """Delete an annotation."""
    service = PaperService(session)
    success = await service.delete_annotation(annotation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return {"success": True}
