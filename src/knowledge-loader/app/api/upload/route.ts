import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Get the document processor URL from environment variable
    const documentProcessorUrl = process.env.DOCUMENT_PROCESSOR_URL || 'http://localhost:8000';
    const uploadEndpoint = `${documentProcessorUrl}/upload`;

    // Get the form data from the request
    const formData = await request.formData();
    const file = formData.get('file');
    const metadataJson = formData.get('metadata') as string | null;
    
    // Create new FormData for the document processor
    const processorFormData = new FormData();
    if (file) {
      processorFormData.append('file', file);
    }
    
    // Parse and add metadata if provided
    if (metadataJson) {
      try {
        const metadata = JSON.parse(metadataJson);
        processorFormData.append('metadata', JSON.stringify(metadata));
      } catch (e) {
        console.error('Failed to parse metadata:', e);
      }
    }
    
    // Forward the request to the document processor API
    const response = await fetch(uploadEndpoint, {
      method: 'POST',
      body: processorFormData,
    });

    // Get the response data
    const data = await response.json();

    // Return the response with the appropriate status code
    if (response.ok) {
      return NextResponse.json(data, { status: response.status });
    } else {
      return NextResponse.json(
        { error: data.detail || 'Upload failed' },
        { status: response.status }
      );
    }
  } catch (error) {
    console.error('Error uploading file:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    );
  }
}
