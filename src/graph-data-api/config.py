"""
Configuration for the Graph Data API.
"""

import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


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
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        # Get Key Vault URL from environment
        key_vault_url = os.getenv("AZURE_KEYVAULT_URL", "https://kv-verida-know-dev.vault.azure.net/")
        
        # Fetch credentials from Azure Key Vault
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
        
        try:
            self.username = secret_client.get_secret("GraphDatabase--Username").value
            self.password = secret_client.get_secret("GraphDatabase--Password").value
        except Exception as e:
            raise ValueError(f"Failed to retrieve Neo4j credentials from Key Vault: {str(e)}")
        
        if not self.uri:
            raise ValueError("NEO4J_URI environment variable is required")
        if not self.username:
            raise ValueError("NEO4J_USERNAME could not be retrieved from Key Vault")
        if not self.password:
            raise ValueError("NEO4J_PASSWORD could not be retrieved from Key Vault")
