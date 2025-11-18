"""
FastAPI application for document chunking.
Provides an endpoint to download documents from Azure Blob Storage.
"""

from io import BytesIO
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from fastapi import FastAPI, HTTPException

from config import AzureBlobStorageConfig
from models import ChunkRequest, ChunkResponse


app = FastAPI(
    title="Chunk API",
    description="API for downloading and chunking documents from Azure Blob Storage",
    version="1.0.0"
)

# Initialize configuration
try:
    config = AzureBlobStorageConfig()
except ValueError as e:
    print(f"Configuration error: {e}")
    config = None


def download_from_blob_storage(document_name: str) -> tuple[bytes, int]:
    """
    Download a document from Azure Blob Storage.
    
    Args:
        document_name: Name of the document to download
        
    Returns:
        Tuple of (document_content, size_in_bytes)
        
    Raises:
        HTTPException: If download fails
    """
    if not config:
        raise HTTPException(
            status_code=500,
            detail="Azure Blob Storage configuration is not properly set"
        )
    
    try:
        # Create blob service client with DefaultAzureCredential
        account_url = f"https://{config.storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=credential
        )
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=config.container_name,
            blob=document_name
        )
        
        # Check if blob exists
        if not blob_client.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_name}' not found in container '{config.container_name}'"
            )
        
        # Download blob
        download_stream = blob_client.download_blob()
        content = download_stream.readall()
        
        return content, len(content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading document from blob storage: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chunk API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    config_status = "configured" if config else "not configured"
    return {
        "status": "healthy",
        "azure_config": config_status
    }


@app.post("/chunk", response_model=ChunkResponse)
async def chunk_document(request: ChunkRequest):
    """
    Download a document from Azure Blob Storage for chunking.
    
    Args:
        request: ChunkRequest containing the document name
        
    Returns:
        ChunkResponse with download information
    """
    try:
        # Download document from blob storage
        content, size_bytes = download_from_blob_storage(request.document_name)
        
        # TODO: Add actual chunking logic here
        # For now, just return download confirmation
        
        return ChunkResponse(
            document_name=request.document_name,
            size_bytes=size_bytes,
            message=f"Document '{request.document_name}' downloaded successfully ({size_bytes} bytes)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error processing document: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
