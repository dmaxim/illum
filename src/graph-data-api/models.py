"""
Pydantic models for the Graph Data API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class BuildGraphRequest(BaseModel):
    """Request model for building a knowledge graph from document chunks."""
    
    document_id: str = Field(..., description="Unique identifier for the document")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9"
            }
        }


class BuildGraphResponse(BaseModel):
    """Response model after building knowledge graph."""
    
    document_id: str = Field(..., description="Document ID")
    doc_type: str = Field(..., description="Type of document (request or response)")
    total_chunks: int = Field(..., description="Total number of chunks processed")
    nodes_created: int = Field(..., description="Total number of nodes created")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9",
                "doc_type": "request",
                "total_chunks": 50,
                "nodes_created": 156,
                "message": "Successfully built knowledge graph for document"
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


class GraphState(BaseModel):
    """State object for LangGraph workflow."""
    
    document_id: str
    doc_type: str
    location: Optional[str] = None
    year: Optional[int] = None
    chunks: List[EmbeddedChunkData]
    nodes_created: int = 0
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
