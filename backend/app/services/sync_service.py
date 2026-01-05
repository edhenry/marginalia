"""Service layer for external system synchronization."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.paper import Paper


class SyncService:
    """Service for syncing with external systems (Notion, Obsidian, arXiv)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # Notion Sync
    async def sync_paper_to_notion(self, paper_id: str) -> dict[str, Any]:
        """Sync a paper to Notion queue database."""
        if not settings.notion_api_key or not settings.notion_queue_database_id:
            return {"error": "Notion not configured"}

        result = await self.session.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings.notion_api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            # Build page properties
            properties = {
                "Title": {"title": [{"text": {"content": paper.title}}]},
                "Authors": {"rich_text": [{"text": {"content": ", ".join(paper.authors)}}]},
                "Status": {"select": {"name": paper.status.value}},
                "Priority": {"number": paper.priority},
                "Year": {"number": paper.year} if paper.year else None,
            }

            # Remove None values
            properties = {k: v for k, v in properties.items() if v is not None}

            if paper.notion_page_id:
                # Update existing page
                response = await client.patch(
                    f"https://api.notion.com/v1/pages/{paper.notion_page_id}",
                    headers=headers,
                    json={"properties": properties},
                )
            else:
                # Create new page
                response = await client.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json={
                        "parent": {"database_id": settings.notion_queue_database_id},
                        "properties": properties,
                    },
                )

            if response.status_code in (200, 201):
                data = response.json()
                paper.notion_page_id = data["id"]
                await self.session.flush()
                return {"success": True, "notion_page_id": data["id"]}
            else:
                return {"error": f"Notion API error: {response.status_code}"}

    async def sync_notion_to_queue(self) -> dict[str, Any]:
        """Pull updates from Notion queue database."""
        if not settings.notion_api_key or not settings.notion_queue_database_id:
            return {"error": "Notion not configured"}

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings.notion_api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            response = await client.post(
                f"https://api.notion.com/v1/databases/{settings.notion_queue_database_id}/query",
                headers=headers,
                json={},
            )

            if response.status_code != 200:
                return {"error": f"Notion API error: {response.status_code}"}

            data = response.json()
            synced_count = 0

            for page in data.get("results", []):
                notion_id = page["id"]

                # Find paper by Notion ID
                result = await self.session.execute(
                    select(Paper).where(Paper.notion_page_id == notion_id)
                )
                paper = result.scalar_one_or_none()

                if paper:
                    # Update from Notion
                    props = page.get("properties", {})
                    if "Priority" in props and props["Priority"].get("number"):
                        paper.priority = props["Priority"]["number"]
                    synced_count += 1

            await self.session.flush()
            return {"success": True, "synced_count": synced_count}

    # Obsidian Sync
    async def write_draft_note(
        self,
        title: str,
        content: str,
        folder: str | None = None,
    ) -> dict[str, Any]:
        """Write a draft note to Obsidian inbox."""
        if not settings.obsidian_vault_path:
            return {"error": "Obsidian vault not configured"}

        vault_path = Path(settings.obsidian_vault_path)
        inbox_folder = folder or settings.obsidian_inbox_folder
        inbox_path = vault_path / inbox_folder

        # Ensure inbox exists
        inbox_path.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
        filename = f"{safe_title}.md"
        filepath = inbox_path / filename

        # Write note
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {"success": True, "path": str(filepath)}

    async def generate_literature_note(self, paper: Paper) -> str:
        """Generate a literature note for a paper."""
        lines = [
            f"# {paper.title}",
            "",
            f"**Authors**: {', '.join(paper.authors)}",
            f"**Year**: {paper.year or 'Unknown'}",
            f"**Venue**: {paper.venue or 'Unknown'}",
            "",
            "## Summary",
            "",
        ]

        if paper.claude_review:
            review = paper.claude_review
            lines.append(review.get("summary", ""))
            lines.append("")
            lines.append("## Key Contributions")
            lines.append("")
            for contrib in review.get("key_contributions", []):
                lines.append(f"- {contrib}")
            lines.append("")
            lines.append("## Relevance")
            lines.append("")
            lines.append(review.get("relevance_analysis", ""))
            lines.append("")
            lines.append("## Discussion Questions")
            lines.append("")
            for q in review.get("discussion_questions", []):
                lines.append(f"- {q}")
        else:
            lines.append(paper.abstract or "No abstract available.")

        lines.extend([
            "",
            "---",
            "",
            f"*Added to library: {paper.added_at.strftime('%Y-%m-%d')}*",
        ])

        return "\n".join(lines)

    async def index_concept_notes(self) -> list[dict[str, str]]:
        """Index concept notes from Obsidian vault."""
        if not settings.obsidian_vault_path:
            return []

        vault_path = Path(settings.obsidian_vault_path)
        concepts_folder = vault_path / settings.obsidian_concepts_folder

        if not concepts_folder.exists():
            return []

        notes = []
        for filepath in concepts_folder.glob("**/*.md"):
            relative_path = filepath.relative_to(vault_path)
            notes.append({
                "title": filepath.stem,
                "path": str(relative_path),
            })

        return notes

    # arXiv / alphaxiv Integration
    async def import_from_arxiv(self, arxiv_id: str) -> dict[str, Any]:
        """Import a paper from arXiv."""
        async with httpx.AsyncClient() as client:
            # Fetch metadata from arXiv API
            response = await client.get(
                f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            )

            if response.status_code != 200:
                return {"error": f"arXiv API error: {response.status_code}"}

            # Parse XML response (simplified)
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            entry = root.find("atom:entry", ns)
            if entry is None:
                return {"error": "Paper not found on arXiv"}

            title = entry.find("atom:title", ns)
            abstract = entry.find("atom:summary", ns)
            authors = entry.findall("atom:author/atom:name", ns)

            paper_data = {
                "title": title.text.strip() if title is not None else "Unknown",
                "abstract": abstract.text.strip() if abstract is not None else None,
                "authors": [a.text for a in authors],
                "source_id": arxiv_id,
                "source_url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            }

            return {"success": True, "paper_data": paper_data}

    async def fetch_pdf_from_url(self, url: str, paper_id: str) -> dict[str, Any]:
        """Fetch and store a PDF from a URL."""
        pdf_dir = Path(settings.pdf_storage_path) / paper_id
        pdf_dir.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)

            if response.status_code != 200:
                return {"error": f"Failed to fetch PDF: {response.status_code}"}

            pdf_path = pdf_dir / "paper.pdf"
            with open(pdf_path, "wb") as f:
                f.write(response.content)

            # Update paper record
            result = await self.session.execute(
                select(Paper).where(Paper.id == paper_id)
            )
            paper = result.scalar_one_or_none()
            if paper:
                paper.pdf_url = str(pdf_path)
                await self.session.flush()

            return {"success": True, "path": str(pdf_path)}
