import logging
from datetime import datetime
from typing import BinaryIO
from azure.storage.blob import BlobServiceClient, BlobClient, ContentSettings
from azure.core.exceptions import AzureError
from config import Settings

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Service for handling Azure Blob Storage operations."""
    
    def __init__(self, settings: Settings):
        """Initialize the blob storage service.
        
        Args:
            settings: Application settings containing Azure connection info
        """
        self.settings = settings
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        self.container_name = settings.azure_storage_container_name
        self._ensure_container_exists()
    
    def _ensure_container_exists(self) -> None:
        """Ensure the blob container exists, create if it doesn't."""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created container: {self.container_name}")
        except AzureError as e:
            logger.error(f"Error ensuring container exists: {e}")
            raise
    
    def upload_file(
        self, 
        file_data: BinaryIO, 
        filename: str,
        content_type: str = "application/octet-stream",
        metadata: dict = None
    ) -> dict:
        """Upload a file to Azure Blob Storage.
        
        Args:
            file_data: Binary file data to upload
            filename: Name of the file
            content_type: MIME type of the file
            metadata: Optional metadata to attach to the blob
            
        Returns:
            Dictionary containing upload details (blob_name, url, upload_time)
            
        Raises:
            AzureError: If upload fails
        """
        try:
            # Generate unique blob name with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            blob_name = f"{timestamp}_{filename}"
            
            # Get blob client
            blob_client: BlobClient = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Set content settings
            content_settings = ContentSettings(content_type=content_type)
            
            # Upload with metadata
            upload_metadata = metadata or {}
            upload_metadata.update({
                "original_filename": filename,
                "upload_time": datetime.utcnow().isoformat()
            })
            
            # Upload the file
            blob_client.upload_blob(
                file_data,
                content_settings=content_settings,
                metadata=upload_metadata,
                overwrite=True
            )
            
            logger.info(f"Successfully uploaded file: {blob_name}")
            
            return {
                "blob_name": blob_name,
                "url": blob_client.url,
                "container": self.container_name,
                "upload_time": upload_metadata["upload_time"],
                "original_filename": filename
            }
            
        except AzureError as e:
            logger.error(f"Error uploading file to blob storage: {e}")
            raise
    
    def delete_file(self, blob_name: str) -> bool:
        """Delete a file from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            AzureError: If deletion fails
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            logger.info(f"Successfully deleted blob: {blob_name}")
            return True
        except AzureError as e:
            logger.error(f"Error deleting blob: {e}")
            raise
