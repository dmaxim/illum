from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure Blob Storage settings
    azure_storage_account_name: str
    azure_storage_container_name: str = "documents"
    
    # API settings
    api_title: str = "Document Processor API"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # File upload settings
    max_file_size_mb: int = 100
    allowed_extensions: list[str] = [
        ".pdf", ".doc", ".docx", ".txt", ".md", 
        ".json", ".xml", ".csv", ".xlsx", ".xls"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    # Override api_port with PORT environment variable if set (for AppHost compatibility)
    if "PORT" in os.environ:
        settings.api_port = int(os.environ["PORT"])
    return settings
