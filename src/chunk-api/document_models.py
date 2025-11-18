"""
Data models for document processing.
"""

from typing import List
from dataclasses import dataclass
from langchain_core.documents import Document


@dataclass
class DocumentPage:
    """Represents a single page with its chunks"""
    page_number: int
    chunks: List[Document]
    content: str


@dataclass
class ProcessedDocument:
    """Represents a processed document with pages and chunks"""
    document_id: str
    document_name: str
    total_pages: int
    pages: List[DocumentPage]
    year: int
    location: str
    doc_type: str
