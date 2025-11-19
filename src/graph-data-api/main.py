"""
FastAPI application for building knowledge graphs from document chunks.
Downloads embedded chunks from Azure Blob Storage and processes them through
a LangGraph pipeline to create graph representations in Neo4j.
"""

import json
import logging
import traceback
from typing import List

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from fastapi import FastAPI, HTTPException

from config import AzureBlobStorageConfig, Neo4jConfig
from models import BuildGraphRequest, BuildGraphResponse, EmbeddedChunkData
from graph_workflow import process_document_chunks

# Load environment variables from a local .env file if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Graph Data API",
    description="API for building knowledge graphs from document chunks stored in Azure Blob Storage",
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
    neo4j_config = Neo4jConfig()
    logger.info("Neo4j configuration loaded successfully")
except ValueError as e:
    logger.error(f"Neo4j configuration error: {e}")
    neo4j_config = None


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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Graph Data API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "azure_blob_config": "configured" if blob_config else "not configured",
        "neo4j_config": "configured" if neo4j_config else "not configured"
    }


@app.post("/build-graph", response_model=BuildGraphResponse)
async def build_graph(request: BuildGraphRequest):
    """
    Download embedded chunks from Azure Blob Storage and build knowledge graph in Neo4j.
    
    This endpoint:
    1. Downloads all embedded chunk JSON files from Azure Blob Storage
    2. Determines the document type (request or response) from chunk metadata
    3. Routes to appropriate graph builder through LangGraph pipeline
    4. Creates nodes and relationships in Neo4j database
    
    Args:
        request: BuildGraphRequest containing document_id
        
    Returns:
        BuildGraphResponse with build summary
    """
    try:
        logger.info(f"Starting graph build request for document_id: {request.document_id}")
        
        if not blob_config:
            logger.error("Blob storage not configured")
            raise HTTPException(status_code=500, detail="Azure Blob Storage is not configured")
        if not neo4j_config:
            logger.error("Neo4j not configured")
            raise HTTPException(status_code=500, detail="Neo4j is not configured")
        
        # 1) Download embedded chunks from blob storage
        logger.info("Step 1: Downloading embedded chunks from blob storage")
        chunks = download_embedded_chunks_from_blob_storage(request.document_id)
        logger.info(f"Downloaded {len(chunks)} embedded chunks")
        
        # 2) Process chunks through LangGraph workflow
        logger.info("Step 2: Processing chunks through LangGraph workflow")
        neo4j_config_dict = {
            "uri": neo4j_config.uri,
            "username": neo4j_config.username,
            "password": neo4j_config.password,
            "database": neo4j_config.database
        }
        
        result = process_document_chunks(
            document_id=request.document_id,
            chunks=chunks,
            neo4j_config=neo4j_config_dict
        )
        
        # Check for errors
        if result.get("error"):
            logger.error(f"Error processing document: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document: {result['error']}"
            )
        
        logger.info(f"Successfully completed graph build for document_id: {request.document_id}")
        
        return BuildGraphResponse(
            document_id=result["document_id"],
            doc_type=result["doc_type"],
            total_chunks=result["total_chunks"],
            nodes_created=result["nodes_created"],
            message=f"Successfully built knowledge graph with {result['nodes_created']} nodes"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing graph build: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error processing graph build: {str(e)}"
        )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
