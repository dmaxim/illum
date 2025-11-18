# Document Processing Pipeline

## Overview

This document processing pipeline uses **LangChain** and **LangGraph** to orchestrate the extraction, processing, and storage of document content. The pipeline automatically routes documents to the appropriate processor (PDF or Word) and stores the results in Azure Blob Storage.

## Architecture

### LangGraph State Machine

The pipeline is implemented as a LangGraph state machine with the following nodes:

1. **Extract Metadata** - Extracts file type and metadata from the document name
2. **Route Processor** - Decides whether to use PDF or Word processor based on file extension
3. **Save Temp File** - Saves downloaded content to a temporary file
4. **Process Document** - Processes the document into pages and chunks using the appropriate processor
5. **Write to Blob** - Writes processed pages and chunks to Azure Blob Storage

### Flow Diagram

```
┌─────────────────────┐
│  Extract Metadata   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Route Processor    │◄─── Determines PDF vs Word
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Save Temp File     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Process Document   │◄─── PDF or Word Processor
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Write to Blob      │◄─── Store pages & chunks
└─────────────────────┘
```

## Components

### 1. Document Processing Pipeline (`document_processing_pipeline.py`)

The main orchestrator that manages the entire workflow using LangGraph.

**Key Features:**
- State management through `PipelineState` TypedDict
- Conditional routing based on file type
- Error handling at each stage
- Automatic temp file cleanup

### 2. Blob Storage Writer (`blob_storage_writer.py`)

Handles writing processed documents to Azure Blob Storage.

**Output Structure:**
```
processed-documents/
  └── {document_id}/
      ├── metadata.json          # Document-level metadata
      ├── pages/
      │   ├── page_0001.json     # Individual page content
      │   ├── page_0002.json
      │   └── ...
      └── chunks/
          ├── chunk_000001.json  # Individual chunks with metadata
          ├── chunk_000002.json
          └── ...
```

### 3. Document Processors

#### PDF Processor (`pdf_document_processor.py`)
- Uses `PyPDFLoader` from LangChain
- Maintains page structure
- Filters out invoice/shipping pages
- Creates chunks with enhanced metadata

#### Word Processor (`word_document_processor.py`)
- Uses `UnstructuredWordDocumentLoader`
- Processes in paged mode
- Smart text cleaning
- Creates chunks with metadata

## API Usage

### Request

```bash
POST /chunk
Content-Type: application/json

{
  "document_name": "example.pdf",
  "location": "California",      # Optional
  "year": 2024,                   # Optional
  "doc_type": "report"            # Optional
}
```

### Response

```json
{
  "document_name": "example.pdf",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "size_bytes": 1048576,
  "total_pages": 42,
  "total_chunks": 156,
  "message": "Document 'example.pdf' processed successfully. 42 pages, 156 chunks written to container 'processed-documents'"
}
```

## Environment Variables

Required environment variables:

```bash
AZURE_STORAGE_ACCOUNT=your_storage_account
AZURE_CONTAINER_NAME=your_input_container
```

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the API

```bash
# Development
python main.py

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Pipeline State

The pipeline maintains state through the `PipelineState` TypedDict:

```python
class PipelineState(TypedDict):
    # Input
    document_name: str
    document_content: bytes
    location: Optional[str]
    year: Optional[int]
    doc_type: Optional[str]
    
    # Intermediate
    metadata: Optional[DocumentMetadata]
    temp_file_path: Optional[str]
    processor_type: Optional[Literal["pdf", "word"]]
    
    # Output
    processed_document: Optional[ProcessedDocument]
    blob_write_result: Optional[dict]
    error: Optional[str]
```

## Error Handling

The pipeline includes comprehensive error handling:

- **File Type Errors**: Returns error if file extension is unsupported
- **Processing Errors**: Catches and reports processor-specific errors
- **Storage Errors**: Handles blob storage write failures
- **Cleanup**: Ensures temporary files are deleted even on error

## Supported File Types

- **PDF**: `.pdf`
- **Word**: `.docx`, `.doc`

## Chunking Configuration

### PDF Documents
- Chunk size: 250 characters
- Chunk overlap: 25 characters
- Separators: `\n\n`, `\n`, ` `, ``

### Word Documents
- Chunk size: 1000 characters
- Chunk overlap: 100 characters
- Separators: `\n\n`, `\n`, ` `, ``

## Metadata

Each chunk includes comprehensive metadata:

```json
{
  "document_id": "uuid",
  "chunk_id": "uuid_index",
  "chunk_index": 0,
  "page": 1,
  "page_number": 1,
  "total_pages": 42,
  "chunk_method": "smart_pdf_processor",
  "char_count": 245,
  "location": "California",
  "year": 2024,
  "doc_type": "report",
  "chunk_size": 250,
  "chunk_overlap": 25
}
```

## Extending the Pipeline

### Adding New Processors

1. Create a new processor class (e.g., `ExcelDocumentProcessor`)
2. Add the file extension check in `_route_processor()`
3. Add processing logic in `_process_document()`
4. Update `PipelineState` if needed

### Custom Blob Output

Override the output container in `BlobStorageWriter`:

```python
writer = BlobStorageWriter()
result = writer.write_processed_document(
    processed_doc,
    output_container="custom-container"
)
```

## Testing

```bash
# Test the health endpoint
curl http://localhost:8000/health

# Test document processing
curl -X POST http://localhost:8000/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "document_name": "test.pdf",
    "location": "California",
    "year": 2024,
    "doc_type": "report"
  }'
```

## Performance Considerations

- **Memory**: Documents are loaded entirely into memory during processing
- **Temp Files**: Created in system temp directory and automatically cleaned up
- **Blob Storage**: Uses Azure DefaultAzureCredential for authentication
- **Parallelization**: Each document is processed sequentially through the pipeline

## Future Enhancements

- [ ] Add support for more document types (Excel, PowerPoint, etc.)
- [ ] Implement async processing for large documents
- [ ] Add vector embedding generation for chunks
- [ ] Support for batch processing multiple documents
- [ ] Add webhook notifications on completion
- [ ] Implement retry logic for transient failures
