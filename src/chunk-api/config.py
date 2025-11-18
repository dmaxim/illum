"""
Configuration for the Chunk API.
"""

import os


class AzureBlobStorageConfig:
    """Configuration for Azure Blob Storage."""
    
    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        self.container_name = os.getenv("AZURE_CONTAINER_NAME")
        
        if not self.storage_account:
            raise ValueError("AZURE_STORAGE_ACCOUNT environment variable is required")
        if not self.container_name:
            raise ValueError("AZURE_CONTAINER_NAME environment variable is required")
