"""
Pydantic models for the Search Data API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class UploadDocumentRequest(BaseModel):
    """Request model for uploading a document to search index."""
    
    document_id: str = Field(..., description="Unique identifier for the document")
    index_name: str = Field(..., description="Name of the Azure AI Search index to upload to")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9",
                "index_name": "document-chunks"
            }
        }


class UploadDocumentResponse(BaseModel):
    """Response model after uploading document chunks to search index."""
    
    document_id: str = Field(..., description="Document ID")
    total_chunks: int = Field(..., description="Total number of chunks uploaded")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9",
                "total_chunks": 50,
                "message": "Successfully uploaded 50 chunks to search index 'document-chunks'"
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
    document_name: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunk_index: Optional[int] = None
    
    class Config:
        extra = "allow"  # Allow additional fields not explicitly defined


class EmbeddedChunkData(BaseModel):
    """Data model for an embedded document chunk."""
    
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    chunk_index: int = Field(..., description="Index of the chunk within the document")
    page_number: int = Field(..., description="Page number where this chunk appears")
    content: str = Field(..., description="Text content of the chunk")
    metadata: ChunkMetadata = Field(..., description="Metadata associated with the chunk")
    embedding: List[float] = Field(..., description="Vector embedding of the chunk content")
    
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
                },
                "embedding": [0.009, -0.031, 0.039]
            }
        }
