"""
Configuration for the Embedding API.
"""

import os
from typing import Optional


class AzureBlobStorageConfig:
    """Configuration for Azure Blob Storage."""
    
    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        # Source container where chunk-api stored chunks
        self.chunks_container = os.getenv("AZURE_STORAGE_CHUNKS_CONTAINER")
        # Destination container for embedded chunks
        # Per requirement, prefer AUZRE_STORAGE_EMBEDDING_CONTAINER (typo preserved),
        # but also support the correctly spelled variable as a fallback.
        self.embedding_container = (
            os.getenv("AZURE_STORAGE_EMBEDDING_CONTAINER")
            or os.getenv("AZURE_STORAGE_EMBEDDING_CONTAINER")
        )
        
        if not self.storage_account:
            raise ValueError("AZURE_STORAGE_ACCOUNT environment variable is required")
        if not self.chunks_container:
            raise ValueError("AZURE_STORAGE_CHUNKS_CONTAINER environment variable is required")
        if not self.embedding_container:
            raise ValueError("AZURE_STORAGE_EMBEDDING_CONTAINER environment variable is required")


class AzureOpenAIConfig:
    """Configuration for Azure OpenAI embeddings."""
    
    def __init__(self,
                 endpoint: Optional[str] = None,
                 api_key: Optional[str] = None,
                 api_version: Optional[str] = None,
                 embedding_deployment: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_VERSION")
        self.embedding_deployment = embedding_deployment or os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        
        if not self.endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
        if not self.api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
        if not self.api_version:
            raise ValueError("AZURE_OPENAI_VERSION environment variable is required")
        if not self.embedding_deployment:
            raise ValueError("AZURE_OPENAI_EMBEDDING_DEPLOYMENT environment variable is required")
