"""
Pydantic models for the Chunk API.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ChunkRequest(BaseModel):
    """Request model for document chunking."""
    
    document_name: str = Field(..., description="Name of the document for processing")
    file_name: str = Field(..., description="Name of the file to download from blob storage")
    location: Optional[str] = Field(None, description="Location/state associated with the document")
    year: Optional[int] = Field(None, description="Year of the document")
    doc_type: Optional[str] = Field(None, description="Type of document")


class ChunkResponse(BaseModel):
    """Response model for document chunking."""
    
    document_name: str
    document_id: str
    size_bytes: int
    total_pages: int
    total_chunks: int
    message: str


class DocumentMetadata(BaseModel):
    """Metadata extracted from document name or blob properties."""
    
    document_name: str
    file_extension: str
    location: Optional[str] = None
    year: Optional[int] = None
    doc_type: Optional[str] = None
