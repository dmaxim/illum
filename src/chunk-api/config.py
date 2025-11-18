"""
Configuration for the Chunk API.
"""

import os


class AzureBlobStorageConfig:
    """Configuration for Azure Blob Storage."""
    
    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        self.source_container = os.getenv("AZURE_STORAGE_SOURCE_CONTAINER")
        self.destination_container = os.getenv("AZURE_STORAGE_DESTINATION_CONTAINER")
        
        if not self.storage_account:
            raise ValueError("AZURE_STORAGE_ACCOUNT environment variable is required")
        if not self.source_container:
            raise ValueError("AZURE_STORAGE_SOURCE_CONTAINER environment variable is required")
        if not self.destination_container:
            raise ValueError("AZURE_STORAGE_DESTINATION_CONTAINER environment variable is required")