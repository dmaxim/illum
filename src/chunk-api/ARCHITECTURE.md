# Document Processing Pipeline - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Chunk API Service                          │
│                         (FastAPI Application)                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ POST /chunk
                                   │ { document_name, location, year, doc_type }
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       1. Download from Blob                         │
│                  (Azure Blob Storage - Input)                        │
│                                                                       │
│  Container: {AZURE_CONTAINER_NAME}                                   │
│  Document: {document_name}                                           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ document_content (bytes)
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  2. LangGraph Processing Pipeline                    │
│                 (DocumentProcessingPipeline)                         │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Node 1: Extract Metadata                                    │   │
│  │  • Parse file extension (.pdf, .docx, .doc)                  │   │
│  │  • Attach optional metadata (location, year, doc_type)       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Node 2: Route Processor                                     │   │
│  │  • .pdf → PDF Processor                                      │   │
│  │  • .docx/.doc → Word Processor                               │   │
│  │  • Other → Error                                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Node 3: Save Temp File                                      │   │
│  │  • Create temporary file with correct extension              │   │
│  │  • Write document content                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Node 4: Process Document                                    │   │
│  │                                                               │   │
│  │  ┌────────────────┐              ┌─────────────────┐         │   │
│  │  │ PDF Processor  │              │ Word Processor  │         │   │
│  │  ├────────────────┤              ├─────────────────┤         │   │
│  │  │ PyPDFLoader    │              │ Unstructured    │         │   │
│  │  │ 250 char chunk │              │ 1000 char chunk │         │   │
│  │  │ 25 char overlap│              │ 100 char overlap│         │   │
│  │  └────────────────┘              └─────────────────┘         │   │
│  │                                                               │   │
│  │  Output: ProcessedDocument                                   │   │
│  │    • document_id                                             │   │
│  │    • pages[] → DocumentPage                                  │   │
│  │      - page_number                                           │   │
│  │      - content                                               │   │
│  │      - chunks[] → Document (LangChain)                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Node 5: Write to Blob                                       │   │
│  │  • Create output container if not exists                     │   │
│  │  • Write metadata.json                                       │   │
│  │  • Write pages/*.json                                        │   │
│  │  • Write chunks/*.json                                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    3. Write to Blob Storage                          │
│                  (Azure Blob Storage - Output)                       │
│                                                                       │
│  Container: processed-documents                                      │
│                                                                       │
│  {document_id}/                                                      │
│    ├── metadata.json                                                 │
│    ├── pages/                                                        │
│    │   ├── page_0001.json                                            │
│    │   ├── page_0002.json                                            │
│    │   └── ...                                                       │
│    └── chunks/                                                       │
│        ├── chunk_000001.json                                         │
│        ├── chunk_000002.json                                         │
│        └── ...                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        4. API Response                               │
│                                                                       │
│  {                                                                   │
│    "document_name": "example.pdf",                                   │
│    "document_id": "uuid",                                            │
│    "size_bytes": 1048576,                                            │
│    "total_pages": 42,                                                │
│    "total_chunks": 156,                                              │
│    "message": "Document processed successfully..."                   │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
src/chunk-api/
│
├── main.py ──────────────────┐ FastAPI Application
│   └── /chunk endpoint       │ • Downloads blob
│       └── Calls pipeline ───┘ • Invokes pipeline
│                                • Returns response
│
├── document_processing_pipeline.py
│   │
│   ├── DocumentProcessingPipeline
│   │   ├── _extract_metadata()     ─┐
│   │   ├── _route_processor()       │ LangGraph Nodes
│   │   ├── _save_temp_file()        │
│   │   ├── _process_document()      │
│   │   └── _write_to_blob()        ─┘
│   │
│   └── PipelineState (TypedDict)   ─── State Management
│
├── pdf_document_processor.py
│   └── PDFDocumentProcessor
│       ├── process_pdf()            ─── Main processing
│       └── _clean_text()            ─── Text cleanup
│
├── word_document_processor.py
│   └── WordDocumentProcessor
│       ├── process_document()       ─── Main processing
│       └── _clean_text()            ─── Text cleanup
│
├── blob_storage_writer.py
│   └── BlobStorageWriter
│       └── write_processed_document()
│           ├── Write metadata.json
│           ├── Write pages/*.json
│           └── Write chunks/*.json
│
├── models.py
│   ├── ChunkRequest               ─── API request model
│   ├── ChunkResponse              ─── API response model
│   └── DocumentMetadata           ─── Pipeline metadata
│
├── document_models.py
│   ├── DocumentPage               ─── Page representation
│   └── ProcessedDocument          ─── Complete document
│
└── config.py
    └── AzureBlobStorageConfig     ─── Environment config
```

## Data Flow

### Input Flow
```
API Request
  │
  ├─► document_name: str
  ├─► location: Optional[str]
  ├─► year: Optional[int]
  └─► doc_type: Optional[str]
        │
        ▼
Blob Download
  │
  └─► document_content: bytes
        │
        ▼
Pipeline Invocation
  │
  └─► PipelineState
        ├─► document_name
        ├─► document_content
        ├─► location
        ├─► year
        └─► doc_type
```

### Processing Flow
```
PipelineState
  │
  ├─► Extract Metadata
  │     └─► metadata: DocumentMetadata
  │           ├─► file_extension
  │           ├─► location
  │           ├─► year
  │           └─► doc_type
  │
  ├─► Route Processor
  │     └─► processor_type: "pdf" | "word"
  │
  ├─► Save Temp File
  │     └─► temp_file_path: str
  │
  ├─► Process Document
  │     └─► processed_document: ProcessedDocument
  │           ├─► document_id: uuid
  │           ├─► document_name
  │           ├─► total_pages
  │           └─► pages: List[DocumentPage]
  │                 ├─► page_number
  │                 ├─► content: str
  │                 └─► chunks: List[Document]
  │                       ├─► page_content: str
  │                       └─► metadata: dict
  │
  └─► Write to Blob
        └─► blob_write_result: dict
              ├─► document_id
              ├─► container
              ├─► uploaded_files
              └─► stats
```

### Output Flow
```
Blob Storage
  │
  └─► processed-documents/
        └─► {document_id}/
              │
              ├─► metadata.json
              │     ├─► document_id
              │     ├─► document_name
              │     ├─► total_pages
              │     ├─► total_chunks
              │     ├─► year
              │     ├─► location
              │     └─► doc_type
              │
              ├─► pages/
              │     └─► page_{NNNN}.json
              │           ├─► page_number
              │           ├─► content
              │           ├─► char_count
              │           └─► chunk_count
              │
              └─► chunks/
                    └─► chunk_{NNNNNN}.json
                          ├─► chunk_id
                          ├─► chunk_index
                          ├─► page_number
                          ├─► content
                          └─► metadata
                                ├─► document_id
                                ├─► page_number
                                ├─► location
                                ├─► year
                                ├─► doc_type
                                ├─► chunk_size
                                └─► chunk_overlap
```

## State Machine Diagram

```
                     START
                       │
                       ▼
             ┌─────────────────┐
             │ Extract Metadata│
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Route Processor │
             └────────┬────────┘
                      │
                 ┌────┴────┐
                 │  Error? │
                 └────┬────┘
                  No  │  Yes
                      │   └──────────► END (Error)
                      ▼
             ┌─────────────────┐
             │ Save Temp File  │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │Process Document │
             └────────┬────────┘
                      │
                 ┌────┴────┐
                 │  Error? │
                 └────┬────┘
                  No  │  Yes
                      │   └──────────► END (Error)
                      ▼
             ┌─────────────────┐
             │ Write to Blob   │
             └────────┬────────┘
                      │
                      ▼
                     END
                  (Success)
```

## Technology Stack

### Core Framework
- **LangGraph 0.2.45** - State machine orchestration
- **LangChain 0.3.7** - Document processing framework
- **FastAPI 0.104.1** - REST API framework
- **Pydantic 2.5.0** - Data validation

### Document Processing
- **PyPDF 5.1.0** - PDF parsing
- **Unstructured 0.16.9** - Document structure extraction
- **python-docx 1.1.2** - Word document processing
- **langchain-text-splitters 0.3.2** - Text chunking

### Azure Integration
- **azure-storage-blob 12.19.0** - Blob storage SDK
- **azure-identity 1.15.0** - Authentication

### Runtime
- **Uvicorn 0.24.0** - ASGI server
- **Python 3.12+** - Runtime environment

## Design Patterns

### 1. State Machine Pattern (LangGraph)
- Explicit state transitions
- Conditional routing
- Error handling at each node

### 2. Strategy Pattern (Processor Selection)
- Runtime selection of processor
- Common interface (ProcessedDocument)
- Easy to extend with new processors

### 3. Builder Pattern (Document Construction)
- Step-by-step document building
- Progressive enhancement of metadata
- Immutable final output

### 4. Repository Pattern (Blob Storage)
- Abstract storage operations
- Consistent interface
- Easy to swap storage backends

## Security Considerations

### Authentication
- Uses Azure DefaultAzureCredential
- Supports multiple auth methods:
  - Azure CLI
  - Managed Identity
  - Service Principal
  - Environment variables

### Data Flow
- Documents processed in memory
- Temporary files cleaned up immediately
- No persistent local storage

### Access Control
- Requires storage account access
- Container-level permissions
- Blob-level read/write operations

## Performance Characteristics

### Throughput
- Sequential processing per instance
- ~2-5 seconds per document
- Scales horizontally

### Memory
- Document loaded entirely in memory
- Typical usage: 50-200 MB per request
- Suitable for documents < 500 MB

### Storage
- Temporary files during processing
- Auto-cleanup on completion
- Minimal disk footprint

## Monitoring & Observability

### Logging Points
- Document download
- Pipeline stage transitions
- Processing errors
- Blob write operations

### Metrics to Track
- Documents processed per hour
- Average processing time per document
- Error rate by document type
- Blob storage write latency

### Error Handling
- Pipeline-level error capture
- Detailed error messages in response
- Cleanup on failure
- No partial writes

## Extensibility

### Adding New Document Types
1. Create processor class
2. Update `_route_processor()` 
3. Update `_process_document()`
4. No changes to pipeline structure

### Custom Output Formats
1. Modify `BlobStorageWriter`
2. Add new write methods
3. Update output structure

### Additional Metadata
1. Extend `DocumentMetadata`
2. Update `PipelineState`
3. Pass through pipeline
4. Include in chunk metadata
