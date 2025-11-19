# Embedding API - Quick Start Guide

## Overview

This API downloads document chunks from Azure Blob Storage, generates embeddings using Azure OpenAI, and writes the embedded chunks back to storage.

## Quick Setup

### 1. Install Dependencies

```bash
cd /Users/mxinfo/storage/github.com/dmaxim/illum/src/embedding-api
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Azure Blob Storage
AZURE_STORAGE_ACCOUNT=your_storage_account_name
AZURE_STORAGE_CHUNKS_CONTAINER=your_chunks_container_name
AUZRE_STORAGE_EMBEDDING_CONTAINER=your_embedding_container_name

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_VERSION=2024-02-01
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your_embedding_deployment_name

# API
PORT=8002
```

### 3. Authenticate with Azure

```bash
az login
```

### 4. Run the API

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --port 8002
```

### 5. Test the API

Check health:
```bash
curl http://localhost:8002/health
```

Embed a document:
```bash
curl -X POST http://localhost:8002/embed \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9",
    "document_name": "Montana-RFP.pdf",
    "total_pages": 24,
    "total_chunks": 50,
    "year": 2025,
    "location": "Montana",
    "doc_type": "request"
  }'
```

Or use the example script:
```bash
python example_usage.py
```

## How It Works

1. **Input**: POST request to `/embed` with document metadata
2. **Download**: API downloads all chunks from `{document_id}/chunks/` in source container
3. **Embed**: Generates embeddings using Azure OpenAI (batched for efficiency)
4. **Write**: Writes chunks with embeddings to `{document_id}/chunk-{index}.json` in destination container
5. **Output**: Response with summary (chunks returned without embeddings for size)

## Output Format

Each embedded chunk JSON file contains:

```json
{
  "chunk_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9_0",
  "chunk_index": 0,
  "page_number": 1,
  "content": "Text content...",
  "metadata": {
    "location": "Montana",
    "year": 2025,
    "doc_type": "request",
    ...
  },
  "embedding": [0.123, -0.456, 0.789, ...]
}
```

## Troubleshooting

### Configuration Errors
- Ensure all environment variables are set
- Check Azure authentication: `az account show`

### Rate Limiting
- The API implements exponential backoff
- Adjust `batch_size` and `pause_every` in `embedder.py` if needed

### Missing Chunks
- Verify chunks exist in source container at `{document_id}/chunks/`
- Check container name matches `AZURE_STORAGE_CHUNKS_CONTAINER`

## Next Steps

- View the [full README](README.md) for detailed documentation
- Check [example_usage.py](example_usage.py) for API client examples
- Integrate embedded chunks with your vector database
