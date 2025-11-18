"""
Pydantic models for the Chunk API.
"""

from pydantic import BaseModel, Field


class ChunkRequest(BaseModel):
    """Request model for document chunking."""
    
    document_name: str = Field(..., description="Name of the document to download from blob storage")


class ChunkResponse(BaseModel):
    """Response model for document chunking."""
    
    document_name: str
    size_bytes: int
    message: str
