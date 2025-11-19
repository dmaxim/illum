# Graph Data API Architecture

## System Architecture

### High-Level Flow

```
Azure Blob Storage (Embeddings Container)
              ↓
    [FastAPI: graph-data-api]
              ↓
      LangGraph Pipeline
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
Request Builder   Response Builder
    ↓                   ↓
       Neo4j Database
```

## LangGraph Workflow Detail

### Workflow Nodes

1. **determine_type** (Entry Point)
   - Reads `doc_type` from chunk metadata
   - Extracts location and year
   - Sets workflow routing

2. **route_by_document_type** (Conditional Edge)
   - Routes to `build_request_graph` if doc_type = "request"
   - Routes to `build_response_graph` if doc_type = "response"
   - Routes to END if error

3. **build_request_graph**
   - Creates: Location, Year, RFP, Document, Page, RequestChunk nodes
   - Establishes relationships between entities
   - Returns node count

4. **build_response_graph**
   - Creates: Document, Page, ResponseChunk nodes
   - Links to existing RFP nodes
   - Returns node count

### State Management

```python
WorkflowState = {
    "document_id": str,
    "doc_type": str,
    "location": str | None,
    "year": int | None,
    "chunks": List[EmbeddedChunkData],
    "nodes_created": int,
    "error": str | None,
    "neo4j_config": dict
}
```

## Graph Schema

### Request Document Graph

```
(Location)-[:HAS_RFP]->(RFP)-[:IS_YEAR]->(Year)
                         ↓
                   [:HAS_DOCUMENT]
                         ↓
                    (Document)-[:HAS_PAGE]->(Page)-[:HAS_CHUNK]->(RequestChunk)
```

**Node Properties:**

- **Location**: `{name: string}`
- **Year**: `{year: string}`
- **RFP**: `{name: string}` (e.g., "Montana RFP 25")
- **Document**: `{name: string, source: string, doc_type: string}`
- **Page**: `{doc_name: string, page_number: int, content: string}`
- **RequestChunk**: `{chunk_id: string, text: string, embedding: float[], doc_name: string, page_number: int, chunk_index: int}`

### Response Document Graph

```
(RFP)-[:HAS_DOCUMENT]->(Document)-[:HAS_PAGE]->(Page)-[:HAS_CHUNK]->(ResponseChunk)
```

**Node Properties:**

- **Document**: `{name: string, source: string, doc_type: string}`
- **Page**: `{doc_name: string, page_number: int, content: string}`
- **ResponseChunk**: `{chunk_id: string, index: int, text: string, embedding: float[], doc_name: string, page_number: int}`

## Comparison: search-data-api vs graph-data-api

### search-data-api

```
Azure Blob Storage → FastAPI → Azure AI Search Index
```

**Purpose:** Full-text and vector search capabilities

**Features:**
- Creates search index with vector embeddings
- Supports hybrid search (text + vector)
- Group-based access control
- Optimized for query performance

### graph-data-api

```
Azure Blob Storage → FastAPI → LangGraph → Neo4j Graph
```

**Purpose:** Relationship-based knowledge representation

**Features:**
- Creates interconnected graph structure
- Supports relationship traversal
- Context-aware querying
- Optimized for relationship discovery

### Common Elements

Both APIs share:
1. **Data Source**: Azure Blob Storage (same chunk format)
2. **Authentication**: DefaultAzureCredential
3. **Structure**: FastAPI, Pydantic models, configuration pattern
4. **Chunk Format**: Same JSON structure with embeddings
5. **Error Handling**: Comprehensive logging and exception handling

## Class Hierarchy

```
GraphBuilder (Base Class)
    ├── execute_query()
    ├── close()
    │
    ├─→ RequestGraphBuilder
    │       ├── create_location_node()
    │       ├── create_year_node()
    │       ├── create_rfp_year_node()
    │       ├── create_rfp_year_location_relationships()
    │       ├── create_document_node()
    │       ├── create_page_nodes()
    │       ├── create_chunk_nodes()
    │       └── build_graph() → int
    │
    └─→ ResponseGraphBuilder
            ├── create_document_node()
            ├── create_page_nodes()
            ├── create_response_chunk_nodes()
            └── build_graph() → int
```

## Processing Pipeline

### Step-by-Step Execution

```
1. API Request
   POST /build-graph
   { "document_id": "..." }

2. Download Phase
   - List blobs in Azure Storage
   - Download JSON files
   - Parse into EmbeddedChunkData

3. LangGraph Workflow
   a. Initialize state
   b. Invoke workflow.compile()
   c. Execute determine_type node
   d. Route to appropriate builder
   e. Execute builder node
   f. Return final state

4. Graph Building
   - Connect to Neo4j
   - Create nodes (MERGE operations)
   - Create relationships
   - Close connection

5. Response
   {
     "document_id": "...",
     "doc_type": "request",
     "total_chunks": 50,
     "nodes_created": 156,
     "message": "..."
   }
```

## Extension Points

### Adding New Document Types

1. Create new builder class extending `GraphBuilder`
2. Implement `build_graph()` method
3. Add routing logic in `route_by_document_type()`
4. Add new node to workflow in `create_graph_workflow()`

### Adding Vector Search

To enable vector similarity search in Neo4j:

```python
def create_vector_index(self):
    query = """
    CREATE VECTOR INDEX request_chunks IF NOT EXISTS
    FOR (c:RequestChunk) ON c.embedding
    OPTIONS {indexConfig: {
      `vector.dimensions`: 1536,
      `vector.similarity_function`: 'cosine'
    }}
    """
    self.execute_query(query)
```

### Adding Graph Analytics

Neo4j Graph Data Science library can be integrated for:
- Community detection
- Path finding
- Centrality analysis
- Similarity algorithms

## Performance Considerations

### Batch Operations

Current implementation processes chunks sequentially. For large documents, consider:
- Batching node creation (UNWIND in Cypher)
- Parallel processing with multiprocessing
- Async Neo4j driver operations

### Memory Management

- Graph builders close connections properly
- Large content is truncated (5000 chars for pages)
- Embeddings stored as arrays (may need optimization)

### Scalability

- Stateless API design (horizontal scaling)
- Neo4j clustering for high availability
- Connection pooling for database access

## Security

### Secrets Management

- Environment variables for configuration
- No secrets in code or logs
- Azure Managed Identity for blob access
- Neo4j authentication required

### Data Access

- Document-level access control in Neo4j
- Audit logging for graph modifications
- Query parameterization to prevent injection

## Monitoring

### Recommended Metrics

1. **API Metrics**
   - Request rate
   - Response time
   - Error rate

2. **Graph Metrics**
   - Nodes created per document
   - Graph build time
   - Neo4j query performance

3. **Resource Metrics**
   - Memory usage
   - Neo4j connection pool
   - Azure Blob bandwidth

## Future Enhancements

1. **Incremental Updates**: Update existing graphs instead of recreating
2. **Validation**: Schema validation for graph structure
3. **Versioning**: Track document versions in graph
4. **Merge Detection**: Identify and merge duplicate entities
5. **Graph Queries API**: Add endpoints for querying the graph
6. **Batch Processing**: Process multiple documents in parallel
7. **Event-Driven**: Trigger on blob upload events
