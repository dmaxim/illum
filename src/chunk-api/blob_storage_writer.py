"""
Module for writing processed documents to Azure Blob Storage.
"""

import json
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

from config import AzureBlobStorageConfig
from document_models import ProcessedDocument


class BlobStorageWriter:
    """Writes processed document pages and chunks to Azure Blob Storage."""
    
    def __init__(self, config: Optional[AzureBlobStorageConfig] = None):
        """
        Initialize the blob storage writer.
        
        Args:
            config: Azure Blob Storage configuration
        """
        self.config = config or AzureBlobStorageConfig()
        account_url = f"https://{self.config.storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=credential
        )
    
    def write_processed_document(
        self, 
        processed_doc: ProcessedDocument,
        output_container: Optional[str] = None
    ) -> dict:
        """
        Write processed document pages and chunks to blob storage.
        
        Args:
            processed_doc: The processed document with pages and chunks
            output_container: Optional output container name (defaults to destination_container from config)
            
        Returns:
            Dictionary with upload statistics and blob URLs
        """
        container_name = output_container or self.config.destination_container
        
        # Ensure container exists
        container_client = self.blob_service_client.get_container_client(container_name)
        try:
            container_client.create_container()
        except Exception:
            # Container already exists
            pass
        
        # Create folder structure: document_id/pages/ and document_id/chunks/
        doc_id = processed_doc.document_id
        
        uploaded_files = {
            "document_metadata": None,
            "pages": [],
            "chunks": []
        }
        
        # 1. Write document metadata
        metadata_blob_name = f"{doc_id}/metadata.json"
        metadata = {
            "document_id": doc_id,
            "document_name": processed_doc.document_name,
            "total_pages": processed_doc.total_pages,
            "year": processed_doc.year,
            "location": processed_doc.location,
            "doc_type": processed_doc.doc_type,
            "total_chunks": sum(len(page.chunks) for page in processed_doc.pages)
        }
        
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=metadata_blob_name
        )
        blob_client.upload_blob(
            json.dumps(metadata, indent=2),
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json")
        )
        uploaded_files["document_metadata"] = metadata_blob_name
        
        # 2. Write each page content
        for page in processed_doc.pages:
            page_blob_name = f"{doc_id}/pages/page_{page.page_number:04d}.json"
            page_data = {
                "page_number": page.page_number,
                "content": page.content,
                "char_count": len(page.content),
                "chunk_count": len(page.chunks)
            }
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=page_blob_name
            )
            blob_client.upload_blob(
                json.dumps(page_data, indent=2),
                overwrite=True,
                content_settings=ContentSettings(content_type="application/json")
            )
            uploaded_files["pages"].append(page_blob_name)
        
        # 3. Write all chunks
        chunk_counter = 0
        for page in processed_doc.pages:
            for chunk in page.chunks:
                chunk_blob_name = f"{doc_id}/chunks/chunk_{chunk_counter:06d}.json"
                chunk_data = {
                    "chunk_id": chunk.metadata.get("chunk_id", f"{doc_id}_{chunk_counter}"),
                    "chunk_index": chunk_counter,
                    "page_number": page.page_number,
                    "content": chunk.page_content,
                    "metadata": chunk.metadata
                }
                
                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name,
                    blob=chunk_blob_name
                )
                blob_client.upload_blob(
                    json.dumps(chunk_data, indent=2),
                    overwrite=True,
                    content_settings=ContentSettings(content_type="application/json")
                )
                uploaded_files["chunks"].append(chunk_blob_name)
                chunk_counter += 1
        
        return {
            "document_id": doc_id,
            "container": container_name,
            "uploaded_files": uploaded_files,
            "stats": {
                "total_pages": len(uploaded_files["pages"]),
                "total_chunks": len(uploaded_files["chunks"])
            }
        }
