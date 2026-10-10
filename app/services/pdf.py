"""PDF text extraction."""

from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf(data: bytes) -> str:
    """Return concatenated text of all pages. Raises on unreadable input."""
    reader = PdfReader(BytesIO(data))
    parts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(parts)
