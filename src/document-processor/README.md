# Document Processor API

A FastAPI-based microservice for uploading documents to Azure Blob Storage. This API is designed to be used by the knowledge-loader to process and store document files.

## Features

- **File Upload**: Upload documents to Azure Blob Storage
- **File Validation**: Validates file types and sizes before upload
- **Azure Integration**: Seamless integration with Azure Blob Storage
- **Health Check**: Built-in health check endpoint
- **Containerized**: Docker support for easy deployment

## Prerequisites

- Python 3.11+
- Azure Storage Account with connection string
- Docker (optional, for containerized deployment)

## Installation

### Local Development

1. Clone the repository and navigate to the document-processor directory:
```bash
cd src/document-processor
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your Azure Storage connection string:
```
AZURE_STORAGE_CONNECTION_STRING=your_actual_connection_string
AZURE_STORAGE_CONTAINER_NAME=documents
```

5. Run the application:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t document-processor:latest .
```

2. Run the container:
```bash
docker run -d \
  --name document-processor \
  -p 8000:8000 \
  -e AZURE_STORAGE_CONNECTION_STRING="your_connection_string" \
  -e AZURE_STORAGE_CONTAINER_NAME="documents" \
  document-processor:latest
```

## API Endpoints

### Health Check
```
GET /health
```

Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "service": "document-processor",
  "version": "1.0.0"
}
```

### Upload Document
```
POST /upload
```

Upload a document file to Azure Blob Storage.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (file upload)

**Supported File Types:**
- `.pdf`, `.doc`, `.docx`
- `.txt`, `.md`
- `.json`, `.xml`
- `.csv`, `.xlsx`, `.xls`

**Response (201 Created):**
```json
{
  "message": "File uploaded successfully",
  "data": {
    "blob_name": "20250118_130000_document.pdf",
    "url": "https://yourstorageaccount.blob.core.windows.net/documents/20250118_130000_document.pdf",
    "container": "documents",
    "upload_time": "2025-01-18T13:00:00.000000",
    "original_filename": "document.pdf"
  }
}
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

**Example using Python requests:**
```python
import requests

url = "http://localhost:8000/upload"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### Delete Document
```
DELETE /documents/{blob_name}
```

Delete a document from Azure Blob Storage.

**Parameters:**
- `blob_name`: The name of the blob to delete

**Response:**
```json
{
  "message": "File deleted successfully",
  "blob_name": "20250118_130000_document.pdf"
}
```

## Configuration

All configuration is managed through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Storage connection string | *Required* |
| `AZURE_STORAGE_CONTAINER_NAME` | Blob container name | `documents` |
| `API_TITLE` | API title | `Document Processor API` |
| `API_VERSION` | API version | `1.0.0` |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `MAX_FILE_SIZE_MB` | Maximum file size in MB | `100` |

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful operation
- `201 Created`: File uploaded successfully
- `400 Bad Request`: Invalid file or missing parameters
- `413 Payload Too Large`: File exceeds maximum size
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Blob storage service not initialized

## Development

### Running Tests

```bash
pytest tests/
```

### API Documentation

Once the server is running, interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Integration with Knowledge-Loader

The knowledge-loader can integrate with this API by sending POST requests to the `/upload` endpoint:

```python
import requests

def upload_to_document_processor(file_path: str, api_url: str = "http://localhost:8000"):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{api_url}/upload", files=files)
        response.raise_for_status()
        return response.json()
```

## License

See the main project LICENSE file for details.
