# Dashboard Services Configuration

## Overview

The AppHost orchestrates all services in the document processing pipeline. Each service is registered with a unique port and configured to work together.

## Service Registry

| Service | Port | Type | Description |
|---------|------|------|-------------|
| document-processor | 8000 | Python FastAPI | PDF document processing and extraction |
| chunk-api | 8001 | Python FastAPI | Document chunking service |
| embedding-api | 8002 | Python FastAPI | Vector embedding generation |
| search-data-api | 8003 | Python FastAPI | Upload chunks to Azure AI Search |
| graph-data-api | 8004 | Python FastAPI | Build knowledge graphs in Neo4j |
| knowledge-loader | 3000 | Next.js | Frontend for document upload/management |
| dashboard | 5000* | Blazor | Monitoring dashboard |

*Dashboard port assigned dynamically by .NET Aspire

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    .NET Aspire AppHost                       │
│                  (Orchestration Layer)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├── document-processor (8000)
                              │   └── Extracts text from PDFs
                              │
                              ├── chunk-api (8001)
                              │   └── Chunks documents → Azure Blob
                              │
                              ├── embedding-api (8002)
                              │   └── Generates embeddings → Azure Blob
                              │
                              ├── search-data-api (8003)
                              │   └── Uploads to Azure AI Search
                              │
                              ├── graph-data-api (8004)
                              │   └── Builds graphs in Neo4j
                              │
                              ├── knowledge-loader (3000)
                              │   └── Web UI for uploads
                              │
                              └── dashboard (dynamic)
                                  └── Monitoring and status
```

## Data Flow

### Standard Processing Pipeline

```
1. Upload (knowledge-loader)
        ↓
2. Process PDF (document-processor)
        ↓
3. Chunk Document (chunk-api)
        ↓
4. Generate Embeddings (embedding-api)
        ↓
        ├─→ 5a. Azure AI Search (search-data-api)
        │
        └─→ 5b. Neo4j Graph (graph-data-api)
```

## Service Details

### document-processor (Port 8000)
- **Path**: `src/document-processor`
- **Virtual Env**: `.venv/bin/python`
- **Purpose**: PDF text extraction and initial processing

### chunk-api (Port 8001)
- **Path**: `src/chunk-api`
- **Virtual Env**: `.venv/bin/python`
- **Environment Variables**:
  - `AZURE_STORAGE_ACCOUNT`: vinfoknowledgedev
  - `AZURE_STORAGE_SOURCE_CONTAINER`: vknowledgeuploaddev
  - `AZURE_STORAGE_DESTINATION_CONTAINER`: vknowledgechunksdev
- **Purpose**: Intelligent document chunking

### embedding-api (Port 8002)
- **Path**: `src/embedding-api`
- **Virtual Env**: `.venv/bin/python`
- **Purpose**: Generate vector embeddings using OpenAI

### search-data-api (Port 8003)
- **Path**: `src/search-data-api`
- **Virtual Env**: `.venv/bin/python`
- **Purpose**: Upload embedded chunks to Azure AI Search index
- **Key Features**:
  - Downloads chunks from Azure Blob Storage
  - Creates/manages search indexes
  - Supports vector and text search
  - Group-based access control

### graph-data-api (Port 8004)
- **Path**: `src/graph-data-api`
- **Virtual Env**: `.venv/bin/python`
- **Purpose**: Build knowledge graphs in Neo4j from document chunks
- **Key Features**:
  - LangGraph workflow orchestration
  - Document type routing (request/response)
  - Creates interconnected graph structures
  - Supports relationship traversal

### knowledge-loader (Port 3000)
- **Path**: `src/knowledge-loader`
- **Type**: Next.js application
- **Environment Variables**:
  - `DOCUMENT_PROCESSOR_URL`: Reference to document-processor endpoint
- **Purpose**: Web UI for document management

### dashboard (Dynamic Port)
- **Path**: `src/dashboard/DocumentProcessing.Dashboard`
- **Type**: Blazor application
- **Purpose**: Monitor all services and system health

## Running the Application

### Start All Services
```bash
cd src/dashboard/DocumentProcessing.Dashboard.AppHost
dotnet run
```

This will start all services simultaneously and display the Aspire dashboard.

### Individual Service Access

Once running, services are accessible at:
- Document Processor: http://localhost:8000
- Chunk API: http://localhost:8001
- Embedding API: http://localhost:8002
- Search Data API: http://localhost:8003
- Graph Data API: http://localhost:8004
- Knowledge Loader: http://localhost:3000
- Dashboard: Check Aspire dashboard for assigned port

### Health Check Endpoints

All FastAPI services provide health checks:
- GET http://localhost:8000/health
- GET http://localhost:8001/health
- GET http://localhost:8002/health
- GET http://localhost:8003/health
- GET http://localhost:8004/health

## Configuration Requirements

### search-data-api Environment Variables
```env
AZURE_STORAGE_ACCOUNT=your_account
AZURE_STORAGE_EMBEDDING_CONTAINER=embeddings
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
GROUP_ACCESS_LIST=group1,group2
```

### graph-data-api Environment Variables
```env
AZURE_STORAGE_ACCOUNT=your_account
AZURE_STORAGE_EMBEDDING_CONTAINER=embeddings
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

## Development Notes

### Virtual Environments
All Python services use `.venv` for dependency isolation. Ensure virtual environments are created before running:

```bash
cd src/search-data-api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

cd ../graph-data-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Adding New Services

To add a new Python FastAPI service:

1. Create service directory under `src/`
2. Set up `.venv` with dependencies
3. Add to `AppHost.cs`:
```csharp
var newService = builder.AddExecutable(
        "new-service",
        Path.GetFullPath("../../new-service/.venv/bin/python"),
        "../../new-service",
        "main.py")
    .WithHttpEndpoint(port: 8005, env: "PORT")
    .WithExternalHttpEndpoints();
```

## Service Dependencies

```
knowledge-loader → document-processor
                ↓
            chunk-api
                ↓
            embedding-api
                ↓
        ┌───────┴────────┐
        ↓                ↓
  search-data-api   graph-data-api
        ↓                ↓
  Azure AI Search   Neo4j Database
```

## Monitoring

The Aspire dashboard provides:
- Service health status
- Logs from all services
- Performance metrics
- Resource utilization
- Endpoint accessibility

Access the dashboard after running `dotnet run` in the AppHost project.
