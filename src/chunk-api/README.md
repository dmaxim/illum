# Chunk API

A FastAPI application for downloading and processing documents from Azure Blob Storage.

## Features

- RESTful API endpoint to download documents from Azure Blob Storage
- Configurable storage account and container via environment variables
- Built-in health check endpoint
- Pydantic models for request/response validation
- Error handling for missing documents and configuration issues

## Prerequisites

- Python 3.8 or higher
- Azure Storage Account with Blob Storage
- Azure Storage Connection String

## Installation

1. Navigate to the chunk-api directory:
```bash
cd src/chunk-api
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Azure Blob Storage credentials:
```
AZURE_STORAGE_ACCOUNT=your_storage_account_name
AZURE_CONTAINER_NAME=your_container_name
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

You can find your connection string in the Azure Portal under:
Storage Account → Access keys → Connection string

## Running the Application

### Development Mode

Run with auto-reload enabled:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or directly with Python:
```bash
python main.py
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Root Endpoint
- **GET** `/`
- Returns API information

**Response:**
```json
{
  "message": "Chunk API is running",
  "version": "1.0.0"
}
```

### Health Check
- **GET** `/health`
- Check API and configuration status

**Response:**
```json
{
  "status": "healthy",
  "azure_config": "configured"
}
```

### Chunk Document
- **POST** `/chunk`
- Download a document from Azure Blob Storage

**Request Body:**
```json
{
  "document_name": "example.pdf"
}
```

**Response:**
```json
{
  "document_name": "example.pdf",
  "size_bytes": 12345,
  "message": "Document 'example.pdf' downloaded successfully (12345 bytes)"
}
```

**Error Responses:**
- `404` - Document not found in blob storage
- `500` - Configuration error or download failure

## API Documentation

Once the application is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Example Usage

### Using cURL

```bash
curl -X POST "http://localhost:8000/chunk" \
  -H "Content-Type: application/json" \
  -d '{"document_name": "example.pdf"}'
```

### Using Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/chunk",
    json={"document_name": "example.pdf"}
)
print(response.json())
```

### Using httpie

```bash
http POST localhost:8000/chunk document_name="example.pdf"
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_STORAGE_ACCOUNT` | Yes | Name of your Azure Storage Account |
| `AZURE_CONTAINER_NAME` | Yes | Name of the blob container |
| `AZURE_STORAGE_CONNECTION_STRING` | Yes | Azure Storage connection string |

## Error Handling

The API provides detailed error messages:
- Missing or invalid configuration
- Document not found in blob storage
- Azure Storage connection issues
- Invalid request format

## Future Enhancements

- Add actual document chunking logic
- Support for different document types (PDF, DOCX, TXT)
- Configurable chunk size and overlap
- Store chunked results in database or return as response
- Authentication and authorization
- Rate limiting

## Development

To add new features or modify the chunking logic, edit the `download_from_blob_storage()` function and the `/chunk` endpoint in `main.py`.

## License

[Add your license here]
