"""
Configuration for the Search Data API.
"""

import os
from typing import List


class AzureBlobStorageConfig:
    """Configuration for Azure Blob Storage."""
    
    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        # Container where embedded chunks are stored
        self.embedding_container = os.getenv("AZURE_STORAGE_EMBEDDING_CONTAINER")
        
        if not self.storage_account:
            raise ValueError("AZURE_STORAGE_ACCOUNT environment variable is required")
        if not self.embedding_container:
            raise ValueError("AZURE_STORAGE_EMBEDDING_CONTAINER environment variable is required")


class AzureSearchConfig:
    """Configuration for Azure AI Search."""
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "document-chunks")
        
        # Parse group access list from comma-delimited environment variable
        group_access_env = os.getenv("GROUP_ACCESS_LIST", "")
        self.group_access_list: List[str] = [
            g.strip() for g in group_access_env.split(",") if g.strip()
        ]
        
        if not self.endpoint:
            raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is required")
        if not self.group_access_list:
            raise ValueError("GROUP_ACCESS_LIST environment variable is required and must contain at least one group")
