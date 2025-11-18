# Knowledge Loader

A Next.js application for uploading documents to a DocumentProcessor API.

## Features

- Browse and select files from the local file system
- Upload documents to a configurable API endpoint
- Real-time upload status feedback
- Support for PDF, DOC, DOCX, TXT, and MD files
- Responsive UI with Tailwind CSS

## Configuration

The DocumentProcessor API URL is configurable via environment variables.

### Environment Variables

Create or update the `.env.local` file in the root directory:

```env
NEXT_PUBLIC_DOCUMENT_PROCESSOR_API_URL=http://localhost:3001/api/process
```

Update this URL to point to your DocumentProcessor API endpoint.

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
4. Click "Upload" to send the file to the DocumentProcessor API
5. View the upload status (success or error messages)

## API Integration

The application sends a POST request to the configured API endpoint with the file as `multipart/form-data`. The DocumentProcessor API should:

- Accept POST requests
- Handle `multipart/form-data` with a `file` field
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
