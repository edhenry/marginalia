"""Service layer for paper operations."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import aiofiles
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.paper import Annotation, AnnotationPosition, Paper, PaperConnection, PaperStatus
from app.schemas.paper import (
    AnnotationCreate,
    AnnotationUpdate,
    PaperCreate,
    PaperUpdate,
)


class PaperService:
    """Service for managing papers and annotations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.pdf_storage_path = Path(settings.pdf_storage_path)
        self.pdf_storage_path.mkdir(parents=True, exist_ok=True)

    async def create_paper(
        self,
        paper_data: PaperCreate,
        pdf_file: BinaryIO | None = None,
        pdf_filename: str | None = None,
    ) -> Paper:
        """Create a new paper."""
        paper_id = str(uuid.uuid4())

        # Handle PDF storage
        if pdf_file:
            pdf_path = await self._store_pdf(paper_id, pdf_file, pdf_filename or "paper.pdf")
        else:
            pdf_path = ""  # Will be filled when PDF is fetched

        paper = Paper(
            id=paper_id,
            title=paper_data.title,
            authors=paper_data.authors,
            venue=paper_data.venue,
            year=paper_data.year,
            abstract=paper_data.abstract,
            pdf_url=pdf_path,
            source_url=paper_data.source_url,
            source_id=paper_data.source_id,
            tags=paper_data.tags,
            status=PaperStatus.NEW,
        )

        self.session.add(paper)
        await self.session.flush()
        return paper

    async def get_paper(self, paper_id: str) -> Paper | None:
        """Get a paper by ID."""
        result = await self.session.execute(
            select(Paper)
            .options(selectinload(Paper.annotations), selectinload(Paper.connections))
            .where(Paper.id == paper_id)
        )
        return result.scalar_one_or_none()

    async def list_papers(
        self,
        status: PaperStatus | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Paper], int]:
        """List papers with optional filters."""
        query = select(Paper).options(selectinload(Paper.annotations))

        if status:
            query = query.where(Paper.status == status)

        if tags:
            # Filter papers that have any of the specified tags
            for tag in tags:
                query = query.where(Paper.tags.contains([tag]))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Paper.priority.desc(), Paper.added_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        papers = list(result.scalars().all())

        return papers, total

    async def update_paper(self, paper_id: str, paper_data: PaperUpdate) -> Paper | None:
        """Update a paper."""
        paper = await self.get_paper(paper_id)
        if not paper:
            return None

        update_data = paper_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(paper, field, value)

        await self.session.flush()
        return paper

    async def delete_paper(self, paper_id: str) -> bool:
        """Delete a paper (or archive it)."""
        paper = await self.get_paper(paper_id)
        if not paper:
            return False

        paper.status = PaperStatus.ARCHIVED
        await self.session.flush()
        return True

    async def get_queue(self) -> dict:
        """Get the prioritized reading queue."""
        # Get papers that are not archived
        active_statuses = [
            PaperStatus.NEW,
            PaperStatus.PROCESSING,
            PaperStatus.CLAUDE_REVIEWED,
            PaperStatus.READING,
        ]

        query = (
            select(Paper)
            .options(selectinload(Paper.annotations))
            .where(Paper.status.in_(active_statuses))
            .order_by(Paper.priority.desc(), Paper.added_at.desc())
        )

        result = await self.session.execute(query)
        papers = list(result.scalars().all())

        # Count by status
        status_counts = {}
        for status in active_statuses:
            status_counts[status.value] = sum(1 for p in papers if p.status == status)

        return {
            "papers": papers,
            "total_count": len(papers),
            "new_count": status_counts.get("new", 0),
            "claude_reviewed_count": status_counts.get("claude_reviewed", 0),
            "reading_count": status_counts.get("reading", 0),
        }

    async def reorder_queue(self, paper_ids: list[str]) -> bool:
        """Reorder papers in the queue."""
        # Assign priorities based on order
        for i, paper_id in enumerate(paper_ids):
            paper = await self.get_paper(paper_id)
            if paper:
                paper.priority = 100 - i  # Higher priority at top
        await self.session.flush()
        return True

    # Annotation methods
    async def create_annotation(
        self, paper_id: str, annotation_data: AnnotationCreate
    ) -> Annotation | None:
        """Create an annotation on a paper."""
        paper = await self.get_paper(paper_id)
        if not paper:
            return None

        annotation_id = str(uuid.uuid4())
        annotation = Annotation(
            id=annotation_id,
            paper_id=paper_id,
            author=annotation_data.author,
            type=annotation_data.type,
            page_number=annotation_data.page_number,
            selected_text=annotation_data.selected_text,
            content=annotation_data.content,
        )

        self.session.add(annotation)

        # Add position if provided
        if annotation_data.position:
            position = AnnotationPosition(
                id=str(uuid.uuid4()),
                annotation_id=annotation_id,
                page_index=annotation_data.position.page_index,
                rects=annotation_data.position.rects,
            )
            self.session.add(position)

        await self.session.flush()
        return annotation

    async def get_annotations(self, paper_id: str) -> list[Annotation]:
        """Get all annotations for a paper."""
        result = await self.session.execute(
            select(Annotation)
            .options(selectinload(Annotation.position))
            .where(Annotation.paper_id == paper_id)
            .order_by(Annotation.page_number, Annotation.created_at)
        )
        return list(result.scalars().all())

    async def update_annotation(
        self, annotation_id: str, annotation_data: AnnotationUpdate
    ) -> Annotation | None:
        """Update an annotation."""
        result = await self.session.execute(
            select(Annotation).where(Annotation.id == annotation_id)
        )
        annotation = result.scalar_one_or_none()
        if not annotation:
            return None

        update_data = annotation_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(annotation, field, value)

        await self.session.flush()
        return annotation

    async def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        result = await self.session.execute(
            select(Annotation).where(Annotation.id == annotation_id)
        )
        annotation = result.scalar_one_or_none()
        if not annotation:
            return False

        await self.session.delete(annotation)
        await self.session.flush()
        return True

    async def _store_pdf(
        self, paper_id: str, pdf_file: BinaryIO, filename: str
    ) -> str:
        """Store a PDF file and return the path."""
        # Create paper-specific directory
        paper_dir = self.pdf_storage_path / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        # Store the file
        pdf_path = paper_dir / filename
        content = pdf_file.read()

        async with aiofiles.open(pdf_path, "wb") as f:
            await f.write(content)

        return str(pdf_path)

    async def get_pdf_path(self, paper_id: str) -> Path | None:
        """Get the path to a paper's PDF."""
        paper = await self.get_paper(paper_id)
        if not paper or not paper.pdf_url:
            return None
        return Path(paper.pdf_url)
