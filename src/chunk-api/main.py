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
from document_processing_pipeline import DocumentProcessingPipeline


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

# Initialize document processing pipeline
pipeline = DocumentProcessingPipeline()


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
    Download and process a document from Azure Blob Storage.
    
    This endpoint:
    1. Downloads the document from blob storage
    2. Runs it through the LangGraph processing pipeline
    3. Extracts metadata and routes to appropriate processor (PDF or Word)
    4. Processes document into pages and chunks
    5. Writes results back to blob storage
    
    Args:
        request: ChunkRequest containing the document name and optional metadata
        
    Returns:
        ChunkResponse with processing results
    """
    try:
        # Download document from blob storage
        content, size_bytes = download_from_blob_storage(request.document_name)
        
        # Run document through processing pipeline
        pipeline_result = pipeline.process(
            document_name=request.document_name,
            document_content=content,
            location=request.location,
            year=request.year,
            doc_type=request.doc_type
        )
        
        # Check for pipeline errors
        if pipeline_result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline error: {pipeline_result['error']}"
            )
        
        # Extract results
        processed_doc = pipeline_result["processed_document"]
        blob_write_result = pipeline_result["blob_write_result"]
        
        total_chunks = sum(len(page.chunks) for page in processed_doc.pages)
        
        return ChunkResponse(
            document_name=request.document_name,
            document_id=processed_doc.document_id,
            size_bytes=size_bytes,
            total_pages=processed_doc.total_pages,
            total_chunks=total_chunks,
            message=f"Document '{request.document_name}' processed successfully. "
                    f"{processed_doc.total_pages} pages, {total_chunks} chunks written to container '{blob_write_result['container']}'"
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
