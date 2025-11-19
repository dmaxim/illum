"""
FastAPI application for uploading document chunks to Azure AI Search.
Downloads embedded chunks from Azure Blob Storage and uploads them to an Azure AI Search index.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from azure.keyvault.secrets import SecretClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchField
)
from fastapi import FastAPI, HTTPException

from config import AzureBlobStorageConfig, AzureSearchConfig
from models import UploadDocumentRequest, UploadDocumentResponse, EmbeddedChunkData

# Load environment variables from a local .env file if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Search Data API",
    description="API for uploading document chunks from Azure Blob Storage to Azure AI Search",
    version="1.0.0"
)

# Initialize configuration
try:
    blob_config = AzureBlobStorageConfig()
    logger.info("Azure Blob Storage configuration loaded successfully")
except ValueError as e:
    logger.error(f"Blob Storage configuration error: {e}")
    blob_config = None

try:
    search_config = AzureSearchConfig()
    logger.info("Azure AI Search configuration loaded successfully")
except ValueError as e:
    logger.error(f"Azure AI Search configuration error: {e}")
    search_config = None


def get_search_admin_key() -> str:
    """
    Retrieve the Azure AI Search admin key from Key Vault.
    
    Returns:
        The admin key as a string
        
    Raises:
        HTTPException: If key retrieval fails
    """
    if not search_config:
        raise HTTPException(
            status_code=500,
            detail="Azure AI Search configuration is not properly set"
        )
    
    try:
        credential = DefaultAzureCredential()
        secret_client = SecretClient(
            vault_url=search_config.key_vault_url,
            credential=credential
        )
        
        secret = secret_client.get_secret("AzureSearch--AdminKey")
        return secret.value
        
    except Exception as e:
        logger.error(f"Error retrieving search admin key from Key Vault: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving search admin key: {str(e)}"
        )


def ensure_search_index_exists(index_name: str):
    """
    Ensure the Azure AI Search index exists with the correct schema.
    Creates the index if it doesn't exist.
    
    Args:
        index_name: Name of the index to ensure exists
    """
    if not search_config:
        raise HTTPException(
            status_code=500,
            detail="Azure AI Search configuration is not properly set"
        )
    
    try:
        # Create index client with admin key for index management
        admin_key = get_search_admin_key()
        credential = AzureKeyCredential(admin_key)
        index_client = SearchIndexClient(
            endpoint=search_config.endpoint,
            credential=credential
        )
        
        # Check if index exists
        try:
            index_client.get_index(index_name)
            logger.info(f"Index '{index_name}' already exists")
            return
        except Exception:
            logger.info(f"Index '{index_name}' does not exist, creating...")
        
        # Define the index schema
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="create_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
            SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
            SearchableField(name="location", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="year", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
            SearchableField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(
                name="group_id",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True
            ),
            SearchField(
                name="vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="vector-profile"
            )
        ]
        
        # Configure vector search
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-algorithm"
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm_configuration_name="hnsw-algorithm"
                )
            ]
        )
        
        # Create the index
        index = SearchIndex(
            name=index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        index_client.create_index(index)
        logger.info(f"Successfully created index '{index_name}'")
        
    except Exception as e:
        logger.error(f"Error ensuring search index exists: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ensuring search index exists: {str(e)}"
        )


def download_embedded_chunks_from_blob_storage(document_id: str) -> List[EmbeddedChunkData]:
    """
    Download all embedded chunk JSON files for a document from Azure Blob Storage.
    
    Args:
        document_id: ID of the document
        
    Returns:
        List of EmbeddedChunkData objects
        
    Raises:
        HTTPException: If download fails
    """
    if not blob_config:
        raise HTTPException(
            status_code=500,
            detail="Azure Blob Storage configuration is not properly set"
        )
    
    try:
        logger.info(f"Downloading embedded chunks for document_id: {document_id}")
        # Create blob service client with DefaultAzureCredential
        account_url = f"https://{blob_config.storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=credential
        )
        
        # Get container client
        container_client = blob_service_client.get_container_client(
            blob_config.embedding_container
        )
        
        # List all blobs in the document's folder
        blob_prefix = f"{document_id}/"
        logger.info(f"Listing blobs with prefix: {blob_prefix}")
        blobs = container_client.list_blobs(name_starts_with=blob_prefix)
        
        chunks = []
        for blob in blobs:
            if blob.name.endswith('.json'):
                logger.debug(f"Downloading blob: {blob.name}")
                # Download the blob
                blob_client = blob_service_client.get_blob_client(
                    container=blob_config.embedding_container,
                    blob=blob.name
                )
                
                download_stream = blob_client.download_blob()
                content = download_stream.readall()
                
                # Parse JSON content
                chunk_data = json.loads(content)
                chunks.append(EmbeddedChunkData(**chunk_data))
        
        if not chunks:
            logger.warning(f"No embedded chunk files found for document_id: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No embedded chunk files found for document_id '{document_id}'"
            )
        
        logger.info(f"Successfully downloaded {len(chunks)} embedded chunks for document_id: {document_id}")
        return chunks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading embedded chunks from blob storage: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading embedded chunks from blob storage: {str(e)}"
        )


def upload_chunks_to_search_index(chunks: List[EmbeddedChunkData], group_access_list: List[str], index_name: str):
    """
    Upload chunks to Azure AI Search index.
    
    Args:
        chunks: List of embedded chunk data
        group_access_list: List of group IDs for access control
        index_name: Name of the index to upload to
        
    Raises:
        HTTPException: If upload fails
    """
    if not search_config:
        raise HTTPException(
            status_code=500,
            detail="Azure AI Search configuration is not properly set"
        )
    
    try:
        logger.info(f"Uploading {len(chunks)} chunks to search index")
        
        # Create search client with admin key
        admin_key = get_search_admin_key()
        credential = AzureKeyCredential(admin_key)
        search_client = SearchClient(
            endpoint=search_config.endpoint,
            index_name=index_name,
            credential=credential
        )
        
        # Prepare documents for upload
        documents = []
        create_date = datetime.utcnow().isoformat() + "Z"
        
        for chunk in chunks:
            document = {
                "id": chunk.chunk_id,
                "document_id": chunk.metadata.document_id,
                "create_date": create_date,
                "page_number": chunk.page_number,
                "location": chunk.metadata.location,
                "year": chunk.metadata.year,
                "doc_type": chunk.metadata.doc_type,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "vector": chunk.embedding,
                "group_id": group_access_list[0]
            }
            documents.append(document)
        
        # Upload documents in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            result = search_client.upload_documents(documents=batch)
            
            # Check for errors
            for item in result:
                if not item.succeeded:
                    logger.error(f"Failed to upload document {item.key}: {item.error_message}")
            
            logger.info(f"Uploaded batch {i // batch_size + 1}/{(len(documents) + batch_size - 1) // batch_size}")
        
        logger.info(f"Successfully uploaded {len(documents)} documents to search index")
        
    except Exception as e:
        logger.error(f"Error uploading chunks to search index: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading chunks to search index: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Search Data API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "azure_blob_config": "configured" if blob_config else "not configured",
        "azure_search_config": "configured" if search_config else "not configured"
    }


@app.post("/upload", response_model=UploadDocumentResponse)
async def upload_document(request: UploadDocumentRequest):
    """
    Download embedded chunks from Azure Blob Storage and upload to Azure AI Search.
    
    This endpoint:
    1. Downloads all embedded chunk JSON files from Azure Blob Storage
    2. Ensures the Azure AI Search index exists with correct schema
    3. Uploads all chunks to the search index with group access control
    
    Args:
        request: UploadDocumentRequest containing document_id
        
    Returns:
        UploadDocumentResponse with upload summary
    """
    try:
        logger.info(f"Starting upload request for document_id: {request.document_id}")
        
        if not blob_config:
            logger.error("Blob storage not configured")
            raise HTTPException(status_code=500, detail="Azure Blob Storage is not configured")
        if not search_config:
            logger.error("Azure AI Search not configured")
            raise HTTPException(status_code=500, detail="Azure AI Search is not configured")
        
        # 1) Download embedded chunks from blob storage
        logger.info("Step 1: Downloading embedded chunks from blob storage")
        chunks = download_embedded_chunks_from_blob_storage(request.document_id)
        logger.info(f"Downloaded {len(chunks)} embedded chunks")
        
        # 2) Ensure search index exists
        logger.info("Step 2: Ensuring search index exists")
        ensure_search_index_exists(request.index_name)
        
        # 3) Upload chunks to search index
        logger.info("Step 3: Uploading chunks to search index")
        upload_chunks_to_search_index(chunks, search_config.group_access_list, request.index_name)
        
        logger.info(f"Successfully completed upload for document_id: {request.document_id}")
        
        return UploadDocumentResponse(
            document_id=request.document_id,
            total_chunks=len(chunks),
            message=f"Successfully uploaded {len(chunks)} chunks to search index '{request.index_name}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing upload: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error processing upload: {str(e)}"
        )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
