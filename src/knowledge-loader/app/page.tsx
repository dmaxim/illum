import FileUploader from '@/components/FileUploader';

export default function Home() {
  const apiUrl = process.env.NEXT_PUBLIC_DOCUMENT_PROCESSOR_API_URL || 'http://localhost:3001/api/process';

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <main className="container mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Knowledge Loader</h1>
          <p className="text-gray-600">Upload documents for processing</p>
        </div>
        <FileUploader apiUrl={apiUrl} />
      </main>
    </div>
  );
}
