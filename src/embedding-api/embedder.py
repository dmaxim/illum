"""
Document embedder using Azure OpenAI.
Based on response_document_embedder.py from verida-rfp-management.
"""

import os
import time
import random
import logging
import httpx
from typing import List, Optional

from openai import AzureOpenAI, RateLimitError

from config import AzureOpenAIConfig

logger = logging.getLogger(__name__)


class DocumentEmbedder:
    """Generates embeddings for document chunks using Azure OpenAI."""
    
    def __init__(self, 
                 config: Optional[AzureOpenAIConfig] = None,
                 batch_size: int = 100,
                 pause_every: int = 300):
        """
        Initialize the DocumentEmbedder with Azure OpenAI credentials.
        
        Args:
            config: AzureOpenAIConfig instance (if None, will try to create from env vars)
            batch_size: Number of chunks to process in each batch (default: 100)
            pause_every: Pause after this many chunks to avoid rate limits (default: 300)
        """
        self.config = config or AzureOpenAIConfig()
        self.batch_size = batch_size
        self.pause_every = pause_every
        
        # Check if SSL verification should be disabled (for self-signed certs or corporate proxies)
        verify_ssl = os.getenv("AZURE_OPENAI_VERIFY_SSL", "true").lower() != "false"
        
        if not verify_ssl:
            logger.warning("SSL verification is DISABLED for Azure OpenAI client")
            # Create custom HTTP client with SSL verification disabled
            http_client = httpx.Client(verify=False)
            self.client = AzureOpenAI(
                azure_endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version,
                http_client=http_client
            )
        else:
            logger.info("SSL verification is enabled for Azure OpenAI client")
            self.client = AzureOpenAI(
                azure_endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version
            )
    
    def _embed_texts_batch(self, texts: List[str], max_retries: int = 5) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with retry logic for rate limiting.
        
        Args:
            texts: List of text strings to embed
            max_retries: Maximum number of retry attempts (default: 5)
            
        Returns:
            List of embedding vectors
            
        Raises:
            RateLimitError: If max retries exceeded
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"Calling Azure OpenAI embeddings API for {len(texts)} texts")
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.config.embedding_deployment,
                )
                logger.debug(f"Successfully received {len(response.data)} embeddings")
                return [item.embedding for item in response.data]
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    # Max retries exceeded, re-raise the error
                    logger.error(f"Max retries ({max_retries}) exceeded for rate limit")
                    raise
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limit hit. Retrying in {wait_time:.2f} seconds (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Error generating embeddings: {str(e)}")
                logger.error(f"Embedding deployment: {self.config.embedding_deployment}")
                logger.error(f"Endpoint: {self.config.endpoint}")
                raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (one per input text)
        """
        text_count = len(texts)
        logger.info(f"Embedding {text_count} chunks...")
        
        embeddings = []
        
        # Process in batches
        for i in range(0, text_count, self.batch_size):
            end_index = min(i + self.batch_size, text_count)
            logger.info(f"Processing chunks {i} to {end_index}")
            
            batch = texts[i:end_index]
            try:
                batch_embeddings = self._embed_texts_batch(batch)
                embeddings.extend(batch_embeddings)
                logger.info(f"Successfully embedded batch {i} to {end_index}")
            except Exception as e:
                logger.error(f"Failed to embed batch {i} to {end_index}: {str(e)}")
                raise
            
            # Pause after every N chunks to avoid rate limits
            if end_index % self.pause_every == 0 and end_index < text_count:
                logger.info("Pausing to avoid rate limits...")
                time.sleep(5)
        
        logger.info("✓ Embedding generation complete")
        
        return embeddings
