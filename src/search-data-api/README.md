# Search Data API

FastAPI service that uploads document chunks from Azure Blob Storage to Azure AI Search.

## Overview

This API downloads embedded document chunks from Azure Blob Storage (container: `vmembeddingchunksdev`) and uploads them to an Azure AI Search index with vector search capabilities.

## Features

- Downloads embedded chunks from Azure Blob Storage
- Automatically creates Azure AI Search index with correct schema
- Uploads chunks with vector embeddings for semantic search
- Supports group-based access control
- Batch processing for efficient uploads

## Setup

### Prerequisites

- Python 3.9+
- Azure Storage Account with embedded chunks
- Azure AI Search service
- Azure credentials configured (DefaultAzureCredential)

### Installation

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_STORAGE_ACCOUNT` | Azure Storage account name | `mystorageaccount` |
| `AZURE_STORAGE_EMBEDDING_CONTAINER` | Container with embedded chunks | `vmembeddingchunksdev` |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search endpoint | `https://mysearch.search.windows.net` |
| `AZURE_SEARCH_API_KEY` | Azure AI Search admin API key | `your-api-key` |
| `AZURE_SEARCH_INDEX_NAME` | Name of the search index | `document-chunks` |
| `GROUP_ACCESS_LIST` | Comma-delimited group IDs | `group1,group2,group3` |
| `PORT` | API server port (optional) | `8003` |

## Usage

### Start the API

```bash
python main.py
```

The API will be available at `http://localhost:8003`

### API Endpoints

#### Health Check
```bash
GET /health
```

Returns the health status and configuration state.

#### Upload Document
```bash
POST /upload
Content-Type: application/json

{
  "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9"
}
```

**Process:**
1. Downloads all embedded chunks for the document from blob storage (pattern: `{document_id}/chunk-*.json`)
2. Ensures the Azure AI Search index exists with correct schema
3. Uploads all chunks to the search index with group access control

**Response:**
```json
{
  "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9",
  "total_chunks": 50,
  "message": "Successfully uploaded 50 chunks to search index 'document-chunks'"
}
```

## Azure AI Search Index Schema

The API automatically creates an index with the following fields:

| Field | Type | Properties |
|-------|------|-----------|
| `id` | String | Key field |
| `document_id` | String | Filterable |
| `create_date` | DateTimeOffset | Filterable, Sortable |
| `page_number` | Int32 | Filterable, Sortable |
| `location` | String | Searchable, Filterable |
| `year` | Int32 | Filterable, Sortable |
| `doc_type` | String | Searchable, Filterable |
| `chunk_index` | Int32 | Filterable, Sortable |
| `content` | String | Searchable |
| `group_id` | Collection(String) | Searchable, Filterable |
| `vector` | Collection(Single) | Vector search (1536 dimensions) |

## Input Data Format

The API expects embedded chunks in Azure Blob Storage with the following structure:

**Blob naming pattern:** `{document_id}/chunk-{index}.json`

**JSON structure:**
```json
{
  "chunk_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9_0",
  "chunk_index": 0,
  "page_number": 1,
  "content": "Document text content...",
  "metadata": {
    "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9",
    "location": "Montana",
    "year": 2025,
    "doc_type": "request",
    ...
  },
  "embedding": [0.009, -0.031, 0.039, ...]
}
```

## Development

### Interactive API Documentation

FastAPI provides automatic interactive documentation:

- Swagger UI: `http://localhost:8003/docs`
- ReDoc: `http://localhost:8003/redoc`

## Error Handling

The API provides detailed error messages for:
- Missing or invalid configuration
- Blob storage access issues
- Search index creation/update failures
- Document upload errors

All errors are logged with full tracebacks for debugging.

## Authentication

The API uses Azure DefaultAzureCredential for authentication, which supports:
- Azure CLI credentials
- Managed Identity
- Environment variables
- Interactive browser authentication
- And more

Ensure your Azure identity has the following permissions:
- **Storage:** `Storage Blob Data Reader` on the embedding container
- **Search:** `Search Service Contributor` or admin API key access
