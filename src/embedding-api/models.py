"""
Pydantic models for the Embedding API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EmbedDocumentRequest(BaseModel):
    """Request model for embedding a document."""
    
    document_id: str = Field(..., description="Unique identifier for the document")
    document_name: str = Field(..., description="Name of the document")
    total_pages: int = Field(..., description="Total number of pages in the document")
    total_chunks: int = Field(..., description="Total number of chunks in the document")
    year: int = Field(..., description="Year associated with the document")
    location: str = Field(..., description="Location associated with the document")
    doc_type: str = Field(..., description="Type of the document (e.g., 'request', 'response')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9",
                "document_name": "Montana-RFP.pdf",
                "total_pages": 24,
                "total_chunks": 50,
                "year": 2025,
                "location": "Montana",
                "doc_type": "request"
            }
        }


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""
    
    producer: Optional[str] = None
    creator: Optional[str] = None
    creationdate: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    moddate: Optional[str] = None
    source: Optional[str] = None
    total_pages: Optional[int] = None
    page: Optional[int] = None
    page_label: Optional[str] = None
    chunk_method: Optional[str] = None
    char_count: Optional[int] = None
    location: Optional[str] = None
    year: Optional[int] = None
    doc_type: Optional[str] = None
    document_id: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunk_index: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields not explicitly defined


class ChunkData(BaseModel):
    """Data model for a document chunk."""
    
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    chunk_index: int = Field(..., description="Index of the chunk within the document")
    page_number: int = Field(..., description="Page number where this chunk appears")
    content: str = Field(..., description="Text content of the chunk")
    metadata: ChunkMetadata = Field(..., description="Metadata associated with the chunk")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9_0",
                "chunk_index": 0,
                "page_number": 1,
                "content": "NEMT Solicitation Scope of Work Page 1 of 24 Contents...",
                "metadata": {
                    "producer": "macOS Version 26.1",
                    "location": "Montana",
                    "year": 2025,
                    "doc_type": "request",
                    "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9"
                }
            }
        }


class EmbedDocumentResponse(BaseModel):
    """Response model after downloading chunks for embedding."""
    
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document name")
    total_pages: int = Field(..., description="Total number of pages")
    total_chunks: int = Field(..., description="Total number of chunks downloaded")
    year: int = Field(..., description="Year associated with the document")
    location: str = Field(..., description="Location associated with the document")
    doc_type: str = Field(..., description="Document type")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9",
                "document_name": "Montana-RFP.pdf",
                "total_pages": 24,
                "total_chunks": 50,
                "year": 2025,
                "location": "Montana",
                "doc_type": "request",
                "chunks": [],
                "message": "Successfully downloaded 50 chunks for document 'Montana-RFP.pdf'"
            }
        }
