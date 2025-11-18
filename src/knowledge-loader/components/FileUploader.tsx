'use client';

import { useState, useRef } from 'react';

interface FileUploaderProps {
  apiUrl: string;
}

export default function FileUploader({ apiUrl }: FileUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | 'info' | null;
    message: string;
  }>({ type: null, message: '' });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus({ type: null, message: '' });
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus({ type: 'error', message: 'Please select a file first' });
      return;
    }

    setUploading(true);
    setUploadStatus({ type: 'info', message: 'Uploading...' });

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setUploadStatus({
          type: 'success',
          message: `File uploaded successfully: ${selectedFile.name}`,
        });
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } else {
        const error = await response.text();
        setUploadStatus({
          type: 'error',
          message: `Upload failed: ${error || response.statusText}`,
        });
      }
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: `Upload error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    } finally {
      setUploading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setUploadStatus({ type: null, message: '' });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Document Upload</h2>

      <div className="space-y-4">
        {/* File Input */}
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.doc,.docx,.txt,.md"
        />

        {/* Browse Button */}
        <div className="flex items-center space-x-4">
          <button
            onClick={handleBrowseClick}
            disabled={uploading}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Browse Files
          </button>
          {selectedFile && (
            <div className="flex-1 text-gray-700">
              <p className="text-sm font-medium">Selected file:</p>
              <p className="text-sm truncate">{selectedFile.name}</p>
              <p className="text-xs text-gray-500">
                {(selectedFile.size / 1024).toFixed(2)} KB
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        {selectedFile && (
          <div className="flex space-x-4">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
            <button
              onClick={handleClear}
              disabled={uploading}
              className="px-6 py-3 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              Clear
            </button>
          </div>
        )}

        {/* Status Message */}
        {uploadStatus.type && (
          <div
            className={`p-4 rounded-md ${
              uploadStatus.type === 'success'
                ? 'bg-green-100 text-green-800'
                : uploadStatus.type === 'error'
                ? 'bg-red-100 text-red-800'
                : 'bg-blue-100 text-blue-800'
            }`}
          >
            {uploadStatus.message}
          </div>
        )}

        {/* API Configuration Display */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            <span className="font-semibold">API Endpoint:</span> {apiUrl}
          </p>
        </div>
      </div>
    </div>
  );
}
