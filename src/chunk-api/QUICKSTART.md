# Quick Start Guide

## Installation

1. **Install dependencies:**
```bash
cd /Users/mxinfo/storage/github.com/dmaxim/illum/src/chunk-api
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export AZURE_STORAGE_ACCOUNT="your_storage_account_name"
export AZURE_CONTAINER_NAME="your_input_container"
```

3. **Authenticate with Azure:**
```bash
# Option 1: Azure CLI
az login

# Option 2: Managed Identity (if running in Azure)
# No additional setup needed

# Option 3: Service Principal
export AZURE_TENANT_ID="your_tenant_id"
export AZURE_CLIENT_ID="your_client_id"
export AZURE_CLIENT_SECRET="your_client_secret"
```

## Running the API

### Development Mode
```bash
python main.py
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing the API

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "azure_config": "configured"
}
```

### 2. Process a PDF Document
```bash
curl -X POST http://localhost:8000/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "document_name": "report.pdf",
    "location": "California",
    "year": 2024,
    "doc_type": "report"
  }'
```

Expected response:
```json
{
  "document_name": "report.pdf",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "size_bytes": 1048576,
  "total_pages": 42,
  "total_chunks": 156,
  "message": "Document 'report.pdf' processed successfully. 42 pages, 156 chunks written to container 'processed-documents'"
}
```

### 3. Process a Word Document
```bash
curl -X POST http://localhost:8000/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "document_name": "policy.docx",
    "location": "Texas",
    "year": 2023,
    "doc_type": "policy"
  }'
```

## What Happens When You Process a Document?

1. **Download**: Document is downloaded from Azure Blob Storage container specified in `AZURE_CONTAINER_NAME`

2. **Extract Metadata**: File extension is detected and optional metadata (location, year, doc_type) is attached

3. **Route**: Pipeline determines which processor to use:
   - `.pdf` → PDF Processor
   - `.docx`, `.doc` → Word Processor

4. **Process**: Document is split into pages and chunks:
   - PDF: 250 char chunks with 25 char overlap
   - Word: 1000 char chunks with 100 char overlap

5. **Write**: Results are written to `processed-documents` container:
   ```
   processed-documents/
     └── {document_id}/
         ├── metadata.json
         ├── pages/
         │   ├── page_0001.json
         │   └── ...
         └── chunks/
             ├── chunk_000001.json
             └── ...
   ```

## Viewing Results

### Using Azure Portal
1. Navigate to your Storage Account
2. Go to "Containers"
3. Open `processed-documents` container
4. Browse by document ID

### Using Azure CLI
```bash
# List all processed documents
az storage blob list \
  --account-name YOUR_STORAGE_ACCOUNT \
  --container-name processed-documents \
  --output table

# Download a specific document's metadata
az storage blob download \
  --account-name YOUR_STORAGE_ACCOUNT \
  --container-name processed-documents \
  --name "{document_id}/metadata.json" \
  --file metadata.json
```

### Using Python
```python
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

# Connect to blob storage
credential = DefaultAzureCredential()
blob_service = BlobServiceClient(
    account_url="https://YOUR_ACCOUNT.blob.core.windows.net",
    credential=credential
)

# List all documents
container = blob_service.get_container_client("processed-documents")
blobs = container.list_blobs()

for blob in blobs:
    if blob.name.endswith("metadata.json"):
        print(f"Document: {blob.name}")
```

## Common Issues

### Issue: "Azure Blob Storage configuration is not properly set"
**Solution**: Make sure environment variables are set:
```bash
echo $AZURE_STORAGE_ACCOUNT
echo $AZURE_CONTAINER_NAME
```

### Issue: "Authentication failed"
**Solution**: Run `az login` or verify your Azure credentials

### Issue: "Document not found in container"
**Solution**: Verify the document exists in the input container:
```bash
az storage blob list \
  --account-name YOUR_STORAGE_ACCOUNT \
  --container-name YOUR_CONTAINER \
  --output table
```

### Issue: "Unsupported file type"
**Solution**: Currently supported formats:
- PDF: `.pdf`
- Word: `.docx`, `.doc`

### Issue: ImportError for langchain or langgraph
**Solution**: Reinstall dependencies:
```bash
pip install -r requirements.txt --upgrade
```

## Next Steps

- Read the full [PIPELINE_README.md](PIPELINE_README.md) for detailed architecture
- Check [example_usage.py](example_usage.py) for programmatic usage
- Customize chunking parameters in processor files
- Add custom metadata fields as needed

## Support

For issues or questions:
1. Check the error message in the API response
2. Review logs in terminal/container logs
3. Verify Azure permissions for storage account access
