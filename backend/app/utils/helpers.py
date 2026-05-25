"""
Shared utility functions for the backend.
"""
import uuid
import re
from typing import Optional
from datetime import datetime, timezone


def generate_id() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Get current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from filenames."""
    # Keep only alphanumerics, dots, dashes, underscores
    safe = re.sub(r'[^\w\-.]', '_', filename)
    # Prevent path traversal
    safe = safe.replace('..', '_')
    return safe[:255]


def format_inr(amount: float) -> str:
    """Format a number as Indian Rupees."""
    if amount >= 10_000_000:
        return f"₹{amount/10_000_000:.2f} Cr"
    if amount >= 100_000:
        return f"₹{amount/100_000:.2f} L"
    if amount >= 1_000:
        return f"₹{amount/1_000:.1f}K"
    return f"₹{amount:,.0f}"


def validate_pan(pan: Optional[str]) -> bool:
    """Validate Indian PAN number format: ABCDE1234F"""
    if not pan:
        return True  # Optional field
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return bool(re.match(pattern, pan.upper()))


def current_financial_year() -> str:
    """Return the current Indian financial year string e.g. '2024-25'."""
    now = utcnow()
    if now.month >= 4:
        return f"{now.year}-{str(now.year + 1)[-2:]}"
    return f"{now.year - 1}-{str(now.year)[-2:]}"


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Simple text chunker for RAG ingestion."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
