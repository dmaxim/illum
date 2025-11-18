# Knowledge Loader

A Next.js application for uploading documents to a DocumentProcessor API.

## Features

- Browse and select files from the local file system
- Upload documents to a configurable API endpoint
- Add custom metadata (key-value pairs) to documents
- Real-time upload status feedback
- Support for PDF, DOC, DOCX, TXT, and MD files
- Responsive UI with Tailwind CSS

## Configuration

The DocumentProcessor API URL is configurable via environment variables.

### Environment Variables

The application uses server-side API routes that forward requests to the DocumentProcessor API. When running through the AppHost, the `DOCUMENT_PROCESSOR_URL` environment variable is automatically configured.

For standalone development, set:

```env
DOCUMENT_PROCESSOR_URL=http://localhost:8000
```

## Getting Started

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Usage

1. Click the "Browse Files" button to open the file picker
2. Select a document from your local file system
3. Review the selected file details (name and size)
4. (Optional) Add metadata key-value pairs:
   - Click "+ Add Field" to add metadata fields
   - Enter a key and value for each metadata field
   - Click the × button to remove metadata fields
   - At least one empty field is always present
5. Click "Upload" to send the file to the DocumentProcessor API
6. View the upload status (success or error messages)

## API Integration

The application uses a Next.js API route (`/api/upload`) that forwards requests to the DocumentProcessor API. The request includes:

- `file`: The document file (multipart/form-data)
- `metadata`: Optional JSON string containing key-value pairs

The DocumentProcessor API should:

- Accept POST requests at `/upload`
- Handle `multipart/form-data` with a `file` field
- Accept optional `metadata` form field (JSON string)
- Return a JSON response on success
- Return appropriate error messages on failure

### Expected API Response

**Success (200 OK):**
```json
{
  "message": "File processed successfully",
  "fileId": "abc123"
}
```

**Error (4xx/5xx):**
```json
{
  "error": "Error message"
}
```

## Tech Stack

- Next.js 16
- TypeScript
- Tailwind CSS
- React 19
