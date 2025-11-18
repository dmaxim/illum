"""
Document embedder using Azure OpenAI.
Based on response_document_embedder.py from verida-rfp-management.
"""

import time
import random
from typing import List, Optional

from openai import AzureOpenAI, RateLimitError

from config import AzureOpenAIConfig


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
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.config.embedding_deployment,
                )
                return [item.embedding for item in response.data]
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    # Max retries exceeded, re-raise the error
                    raise
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit hit. Retrying in {wait_time:.2f} seconds (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (one per input text)
        """
        text_count = len(texts)
        print(f"Embedding {text_count} chunks...")
        
        embeddings = []
        
        # Process in batches
        for i in range(0, text_count, self.batch_size):
            end_index = min(i + self.batch_size, text_count)
            print(f"Processing chunks {i} to {end_index}")
            
            batch = texts[i:end_index]
            batch_embeddings = self._embed_texts_batch(batch)
            embeddings.extend(batch_embeddings)
            
            # Pause after every N chunks to avoid rate limits
            if end_index % self.pause_every == 0 and end_index < text_count:
                print("Pausing to avoid rate limits...")
                time.sleep(5)
        
        print("✓ Embedding generation complete")
        
        return embeddings
