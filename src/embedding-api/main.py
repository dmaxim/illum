"""
FastAPI application for document embedding.
Provides an endpoint to download chunk files, generate embeddings, and write embedded chunks.
"""

import json
import logging
import traceback
from typing import List

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import FastAPI, HTTPException

from config import AzureBlobStorageConfig, AzureOpenAIConfig
from models import EmbedDocumentRequest, EmbedDocumentResponse, ChunkData
from embedder import DocumentEmbedder

# Load environment variables from a local .env file if present
# This ensures the app picks up configuration when launched by Aspire
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Embedding API",
    description="API for downloading document chunks and processing embeddings",
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
    openai_config = AzureOpenAIConfig()
    logger.info("Azure OpenAI configuration loaded successfully")
except ValueError as e:
    logger.error(f"Azure OpenAI configuration error: {e}")
    openai_config = None

# Initialize embedder
embedder = DocumentEmbedder(config=openai_config) if openai_config else None
if embedder:
    logger.info("Document embedder initialized successfully")
else:
    logger.warning("Document embedder not initialized - check OpenAI configuration")


def download_chunks_from_blob_storage(document_id: str) -> List[ChunkData]:
    """
    Download all chunk.json files for a document from Azure Blob Storage.
    
    Args:
        document_id: ID of the document
        
    Returns:
        List of ChunkData objects
        
    Raises:
        HTTPException: If download fails
    """
    if not blob_config:
        raise HTTPException(
            status_code=500,
            detail="Azure Blob Storage configuration is not properly set"
        )
    
    try:
        logger.info(f"Downloading chunks for document_id: {document_id}")
        # Create blob service client with DefaultAzureCredential
        account_url = f"https://{blob_config.storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=credential
        )
        
        # Get container client
        container_client = blob_service_client.get_container_client(
            blob_config.chunks_container
        )
        
        # List all blobs in the document's chunks folder
        blob_prefix = f"{document_id}/chunks/"
        logger.info(f"Listing blobs with prefix: {blob_prefix}")
        blobs = container_client.list_blobs(name_starts_with=blob_prefix)
        
        chunks = []
        for blob in blobs:
            if blob.name.endswith('.json'):
                logger.debug(f"Downloading blob: {blob.name}")
                # Download the blob
                blob_client = blob_service_client.get_blob_client(
                    container=blob_config.chunks_container,
                    blob=blob.name
                )
                
                download_stream = blob_client.download_blob()
                content = download_stream.readall()
                
                # Parse JSON content
                chunk_data = json.loads(content)
                chunks.append(ChunkData(**chunk_data))
        
        if not chunks:
            logger.warning(f"No chunk files found for document_id: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No chunk files found for document_id '{document_id}'"
            )
        
        logger.info(f"Successfully downloaded {len(chunks)} chunks for document_id: {document_id}")
        return chunks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading chunks from blob storage: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading chunks from blob storage: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Embedding API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "azure_blob_config": "configured" if blob_config else "not configured",
        "azure_openai_config": "configured" if openai_config else "not configured"
    }


@app.post("/embed", response_model=EmbedDocumentResponse)
async def embed_document(request: EmbedDocumentRequest):
    """
    Download chunk files for a document, generate embeddings, and write embedded chunks.
    
    This endpoint:
    1. Takes document metadata (document_id, etc.)
    2. Downloads all chunk.json files from Azure Blob Storage (source container)
    3. Generates embeddings for each chunk's content using Azure OpenAI
    4. Writes each chunk as JSON to the embedding container with an added `embedding` field
       - Blob name format: `{document_id}/chunk-{chunkIndex}.json`
    
    Args:
        request: EmbedDocumentRequest containing document metadata
        
    Returns:
        EmbedDocumentResponse with summary and original chunks (without embedding)
    """
    try:
        logger.info(f"Starting embed request for document_id: {request.document_id}")
        
        if not embedder:
            logger.error("Embedder not configured")
            raise HTTPException(status_code=500, detail="Azure OpenAI embedding is not configured")
        if not blob_config:
            logger.error("Blob storage not configured")
            raise HTTPException(status_code=500, detail="Azure Blob Storage is not configured")
        
        # 1) Download all chunks for the document
        logger.info("Step 1: Downloading chunks from blob storage")
        chunks = download_chunks_from_blob_storage(request.document_id)
        logger.info(f"Downloaded {len(chunks)} chunks")
        
        # 2) Generate embeddings
        logger.info("Step 2: Generating embeddings")
        texts = [c.content for c in chunks]
        logger.info(f"Extracted {len(texts)} text chunks for embedding")
        embeddings = embedder.embed_texts(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # 3) Write embedded chunks to destination container
        logger.info("Step 3: Writing embedded chunks to destination container")
        account_url = f"https://{blob_config.storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
        container_client = blob_service_client.get_container_client(blob_config.embedding_container)
        try:
            container_client.create_container()
            logger.info(f"Created container: {blob_config.embedding_container}")
        except Exception as e:
            logger.debug(f"Container already exists or creation failed: {e}")
        
        uploaded = []
        for idx, (c, emb) in enumerate(zip(chunks, embeddings)):
            try:
                # Build json payload including embedding
                payload = {
                    "chunk_id": c.chunk_id,
                    "chunk_index": c.chunk_index,
                    "page_number": c.page_number,
                    "content": c.content,
                    "metadata": c.metadata.model_dump() if hasattr(c.metadata, "model_dump") else dict(c.metadata),
                    "embedding": emb,
                }
                blob_name = f"{request.document_id}/chunk-{c.chunk_index}.json"
                blob_client = blob_service_client.get_blob_client(
                    container=blob_config.embedding_container,
                    blob=blob_name
                )
                blob_client.upload_blob(
                    json.dumps(payload, ensure_ascii=False),
                    overwrite=True,
                    content_settings=ContentSettings(content_type="application/json")
                )
                uploaded.append(blob_name)
                logger.debug(f"Uploaded chunk {idx + 1}/{len(chunks)}: {blob_name}")
            except Exception as chunk_error:
                logger.error(f"Error uploading chunk {idx}: {str(chunk_error)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
        
        logger.info(f"Successfully uploaded {len(uploaded)} embedded chunks")
        
        return EmbedDocumentResponse(
            document_id=request.document_id,
            document_name=request.document_name,
            total_pages=request.total_pages,
            total_chunks=len(chunks),
            year=request.year,
            location=request.location,
            doc_type=request.doc_type,
            chunks=chunks,
            message=f"Embedded {len(chunks)} chunks and wrote to container '{blob_config.embedding_container}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing document: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error processing document: {str(e)}"
        )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
