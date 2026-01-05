"""Service for PDF processing and text extraction."""

from pathlib import Path
from typing import Optional

from pypdf import PdfReader


class PDFService:
    """Service for extracting text and metadata from PDFs."""

    def extract_text(
        self,
        pdf_path: str | Path,
        start_page: int = 0,
        end_page: Optional[int] = None,
        max_chars: int = 100000,
    ) -> str:
        """
        Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            start_page: Starting page (0-indexed)
            end_page: Ending page (exclusive), None for all pages
            max_chars: Maximum characters to extract

        Returns:
            Extracted text as a string
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)

        if end_page is None or end_page > num_pages:
            end_page = num_pages

        text_parts = []
        total_chars = 0

        for page_num in range(start_page, end_page):
            page = reader.pages[page_num]
            page_text = page.extract_text() or ""

            # Add page marker
            text_parts.append(f"\n--- Page {page_num + 1} ---\n")
            text_parts.append(page_text)

            total_chars += len(page_text)
            if total_chars >= max_chars:
                text_parts.append("\n[Text truncated due to length...]")
                break

        return "\n".join(text_parts)

    def extract_text_by_pages(
        self,
        pdf_path: str | Path,
    ) -> list[dict]:
        """
        Extract text from each page of a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of dicts with page_number and text
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        reader = PdfReader(pdf_path)
        pages = []

        for i, page in enumerate(reader.pages):
            pages.append({
                "page_number": i + 1,
                "text": page.extract_text() or "",
            })

        return pages

    def get_metadata(self, pdf_path: str | Path) -> dict:
        """
        Extract metadata from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with metadata
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        reader = PdfReader(pdf_path)
        metadata = reader.metadata or {}

        return {
            "title": metadata.get("/Title", ""),
            "author": metadata.get("/Author", ""),
            "subject": metadata.get("/Subject", ""),
            "creator": metadata.get("/Creator", ""),
            "producer": metadata.get("/Producer", ""),
            "creation_date": str(metadata.get("/CreationDate", "")),
            "modification_date": str(metadata.get("/ModDate", "")),
            "num_pages": len(reader.pages),
        }

    def get_page_count(self, pdf_path: str | Path) -> int:
        """Get the number of pages in a PDF."""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        reader = PdfReader(pdf_path)
        return len(reader.pages)


# Singleton instance
pdf_service = PDFService()
