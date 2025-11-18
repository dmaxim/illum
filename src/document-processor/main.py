import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from azure.core.exceptions import AzureError

from config import Settings, get_settings
from blob_service import BlobStorageService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global blob service instance
blob_service: Optional[BlobStorageService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global blob_service
    settings = get_settings()
    
    # Startup
    logger.info("Starting Document Processor API")
    blob_service = BlobStorageService(settings)
    logger.info("Blob storage service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Document Processor API")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)


def get_blob_service() -> BlobStorageService:
    """Dependency to get blob service instance."""
    if blob_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blob storage service not initialized"
        )
    return blob_service


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "document-processor",
        "version": settings.api_version
    }


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    blob_service: BlobStorageService = Depends(get_blob_service)
):
    """Upload a document to Azure Blob Storage.
    
    Args:
        file: The file to upload
        blob_service: Injected blob storage service
        
    Returns:
        JSON response with upload details
        
    Raises:
        HTTPException: If file validation fails or upload errors occur
    """
    settings = get_settings()
    
    # Validate file exists
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
        )
    
    # Validate file size
    file_size = 0
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    
    try:
        # Read file content
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
            )
        
        # Upload to blob storage
        from io import BytesIO
        file_data = BytesIO(contents)
        
        upload_result = blob_service.upload_file(
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            metadata={
                "file_size": str(file_size)
            }
        )
        
        logger.info(f"File uploaded successfully: {file.filename} -> {upload_result['blob_name']}")
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "File uploaded successfully",
                "data": upload_result
            }
        )
        
    except AzureError as e:
        logger.error(f"Azure storage error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
    finally:
        await file.close()


@app.delete("/documents/{blob_name}")
async def delete_document(
    blob_name: str,
    blob_service: BlobStorageService = Depends(get_blob_service)
):
    """Delete a document from Azure Blob Storage.
    
    Args:
        blob_name: Name of the blob to delete
        blob_service: Injected blob storage service
        
    Returns:
        JSON response confirming deletion
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        blob_service.delete_file(blob_name)
        return {
            "message": "File deleted successfully",
            "blob_name": blob_name
        }
    except AzureError as e:
        logger.error(f"Azure storage error during deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
