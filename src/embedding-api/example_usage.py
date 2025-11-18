"""
Example usage of the Embedding API.
This script demonstrates how to call the /embed endpoint.
"""

import requests
import json
from typing import Dict, Any


def embed_document(
    document_id: str,
    document_name: str,
    total_pages: int,
    total_chunks: int,
    year: int,
    location: str,
    doc_type: str,
    api_base_url: str = "http://localhost:8002"
) -> Dict[str, Any]:
    """
    Call the embedding API to process a document.
    
    Args:
        document_id: Unique identifier for the document
        document_name: Name of the document
        total_pages: Total number of pages in the document
        total_chunks: Total number of chunks
        year: Year associated with the document
        location: Location associated with the document
        doc_type: Type of the document
        api_base_url: Base URL of the embedding API
        
    Returns:
        Response from the API
    """
    url = f"{api_base_url}/embed"
    
    payload = {
        "document_id": document_id,
        "document_name": document_name,
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "year": year,
        "location": location,
        "doc_type": doc_type
    }
    
    print(f"Calling embedding API for document: {document_name}")
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Success!")
        print(f"  Document ID: {result['document_id']}")
        print(f"  Total chunks processed: {result['total_chunks']}")
        print(f"  Message: {result['message']}")
        return result
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"  {response.text}")
        return None


def check_health(api_base_url: str = "http://localhost:8002") -> Dict[str, Any]:
    """
    Check the health status of the API.
    
    Args:
        api_base_url: Base URL of the embedding API
        
    Returns:
        Health status response
    """
    url = f"{api_base_url}/health"
    response = requests.get(url)
    
    if response.status_code == 200:
        health = response.json()
        print("Health Check:")
        print(f"  Status: {health['status']}")
        print(f"  Azure Blob Config: {health['azure_blob_config']}")
        print(f"  Azure OpenAI Config: {health['azure_openai_config']}")
        return health
    else:
        print(f"Health check failed: {response.status_code}")
        return None


if __name__ == "__main__":
    # Example usage
    API_BASE_URL = "http://localhost:8002"
    
    # Check health first
    print("=" * 60)
    check_health(API_BASE_URL)
    print("=" * 60)
    print()
    
    # Example document
    result = embed_document(
        document_id="9b7b3e33-07da-4fe5-9467-6de3074e26c9",
        document_name="Montana-RFP.pdf",
        total_pages=24,
        total_chunks=50,
        year=2025,
        location="Montana",
        doc_type="request",
        api_base_url=API_BASE_URL
    )
    
    if result:
        print(f"\n✓ Embedding process completed successfully!")
        print(f"  Check Azure Storage container for embedded chunks at:")
        print(f"  {result['document_id']}/chunk-0.json")
        print(f"  {result['document_id']}/chunk-1.json")
        print(f"  ...")
