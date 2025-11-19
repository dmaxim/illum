"""
Configuration for the Graph Data API.
"""

import os


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


class Neo4jConfig:
    """Configuration for Neo4j database."""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        if not self.uri:
            raise ValueError("NEO4J_URI environment variable is required")
        if not self.username:
            raise ValueError("NEO4J_USERNAME environment variable is required")
        if not self.password:
            raise ValueError("NEO4J_PASSWORD environment variable is required")
