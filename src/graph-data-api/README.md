# Graph Data API

FastAPI application for building knowledge graphs from document chunks stored in Azure Blob Storage and writing them to a Neo4j database using LangGraph pipelines.

## Overview

The Graph Data API:
1. Downloads embedded document chunks from Azure Blob Storage
2. Determines the document type (request or response) from metadata
3. Routes processing through a LangGraph pipeline
4. Builds appropriate graph structures in Neo4j based on document type

## Architecture

### Components

- **FastAPI Application** (`main.py`): RESTful API with endpoints for graph building
- **LangGraph Workflow** (`graph_workflow.py`): Pipeline that routes documents based on type
- **Graph Builders** (`graph_builder.py`): 
  - `RequestGraphBuilder`: Builds graphs for RFP request documents
  - `ResponseGraphBuilder`: Builds graphs for RFP response documents
- **Models** (`models.py`): Pydantic models for request/response validation
- **Configuration** (`config.py`): Environment-based configuration

### LangGraph Pipeline Flow

```
1. Download Chunks → 2. Determine Type → 3. Route by Type → 4. Build Graph
                                              ↓
                                    ┌─────────┴─────────┐
                                    ↓                   ↓
                          Request Builder    Response Builder
                                    ↓                   ↓
                              Neo4j Graph         Neo4j Graph
```

## Graph Structure

### Request Documents (doc_type = "request")

Creates the following node types and relationships:
- **Location** → HAS_RFP → **RFP**
- **RFP** → IS_YEAR → **Year**
- **RFP** → HAS_DOCUMENT → **Document**
- **Document** → HAS_PAGE → **Page**
- **Page** → HAS_CHUNK → **RequestChunk**

### Response Documents (doc_type = "response")

Creates the following node types and relationships:
- **RFP** → HAS_DOCUMENT → **Document**
- **Document** → HAS_PAGE → **Page**
- **Page** → HAS_CHUNK → **ResponseChunk**

## Installation

### Prerequisites

- Python 3.9+
- Neo4j database (local or cloud)
- Azure Blob Storage account
- Azure credentials configured (DefaultAzureCredential)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Edit `.env` with your configuration:
```env
# Azure Blob Storage
AZURE_STORAGE_ACCOUNT=your_storage_account
AZURE_STORAGE_EMBEDDING_CONTAINER=embeddings

# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# OpenAI (if needed for future LLM features)
OPENAI_API_KEY=your_openai_api_key
```

## Usage

### Start the Server

```bash
# Default port 8004
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

### API Endpoints

#### Health Check
```bash
GET /health
```

Returns the health status and configuration state.

#### Build Knowledge Graph
```bash
POST /build-graph
Content-Type: application/json

{
  "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9"
}
```

**Response:**
```json
{
  "document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9",
  "doc_type": "request",
  "total_chunks": 50,
  "nodes_created": 156,
  "message": "Successfully built knowledge graph with 156 nodes"
}
```

### Example with cURL

```bash
curl -X POST "http://localhost:8004/build-graph" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "9b7b3e33-07da-4fe5-9467-6de3074e26c9"}'
```

## Data Format

### Input Data Structure

The API expects chunks stored in Azure Blob Storage with the following structure:

```
container/
  document_id/
    chunk_0.json
    chunk_1.json
    ...
```

Each chunk JSON file should contain:
```json
{
  "chunk_id": "doc_id_0",
  "chunk_index": 0,
  "page_number": 1,
  "content": "Text content of the chunk",
  "metadata": {
    "location": "Montana",
    "year": 2025,
    "doc_type": "request",
    "document_id": "doc_id",
    "title": "Document Title"
  },
  "embedding": [0.009, -0.031, ...]
}
```

### Document Types

The `doc_type` field in the metadata determines routing:
- `"request"`: RFP request documents → `RequestGraphBuilder`
- `"response"`: RFP response documents → `ResponseGraphBuilder`

## Development

### Project Structure

```
src/graph-data-api/
├── main.py              # FastAPI application
├── graph_workflow.py    # LangGraph pipeline
├── graph_builder.py     # Graph builder classes
├── models.py            # Pydantic models
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── .env.example         # Example environment variables
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests (when tests are created)
pytest
```

## Relationship to search-data-api

This API follows the same structure as `search-data-api` but:
- **search-data-api**: Downloads chunks → Uploads to Azure AI Search
- **graph-data-api**: Downloads chunks → Builds graph → Writes to Neo4j

Both APIs share:
- Same data source (Azure Blob Storage)
- Same chunk format
- Similar configuration approach
- Similar error handling and logging

## Neo4j Queries

After building graphs, you can query Neo4j:

### Find all RFPs
```cypher
MATCH (r:Rfp) RETURN r
```

### Find all documents for a location
```cypher
MATCH (l:Location {name: "Montana"})-[:HAS_RFP]->(r:Rfp)-[:HAS_DOCUMENT]->(d:Document)
RETURN d
```

### Find chunks with similar content (requires vector index)
```cypher
MATCH (c:RequestChunk)
WHERE c.doc_name = "Montana-RFP"
RETURN c.text, c.page_number
```

## License

Same as parent project.
