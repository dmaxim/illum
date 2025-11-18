"""
Example usage of the document processing pipeline.

This script demonstrates how to use the pipeline programmatically
without going through the FastAPI endpoint.
"""

from document_processing_pipeline import DocumentProcessingPipeline


def example_process_pdf():
    """Example: Process a PDF document."""
    
    # Initialize pipeline
    pipeline = DocumentProcessingPipeline()
    
    # Read document content (in real usage, this would come from blob storage)
    with open("example.pdf", "rb") as f:
        document_content = f.read()
    
    # Process document
    result = pipeline.process(
        document_name="example.pdf",
        document_content=document_content,
        location="California",
        year=2024,
        doc_type="annual_report"
    )
    
    # Check results
    if result.get("error"):
        print(f"Error: {result['error']}")
        return
    
    # Extract results
    processed_doc = result["processed_document"]
    blob_result = result["blob_write_result"]
    
    print(f"Document processed successfully!")
    print(f"Document ID: {processed_doc.document_id}")
    print(f"Total Pages: {processed_doc.total_pages}")
    print(f"Total Chunks: {sum(len(page.chunks) for page in processed_doc.pages)}")
    print(f"Written to container: {blob_result['container']}")
    print(f"Metadata blob: {blob_result['uploaded_files']['document_metadata']}")


def example_process_word():
    """Example: Process a Word document."""
    
    # Initialize pipeline
    pipeline = DocumentProcessingPipeline()
    
    # Read document content
    with open("example.docx", "rb") as f:
        document_content = f.read()
    
    # Process document
    result = pipeline.process(
        document_name="example.docx",
        document_content=document_content,
        location="Texas",
        year=2023,
        doc_type="policy_document"
    )
    
    # Check results
    if result.get("error"):
        print(f"Error: {result['error']}")
        return
    
    # Extract results
    processed_doc = result["processed_document"]
    
    print(f"Document processed successfully!")
    print(f"Document ID: {processed_doc.document_id}")
    
    # Print page information
    for page in processed_doc.pages:
        print(f"Page {page.page_number}: {len(page.chunks)} chunks")


def example_inspect_chunks():
    """Example: Inspect chunks from a processed document."""
    
    from document_processing_pipeline import DocumentProcessingPipeline
    
    pipeline = DocumentProcessingPipeline()
    
    # Process a document
    with open("example.pdf", "rb") as f:
        document_content = f.read()
    
    result = pipeline.process(
        document_name="example.pdf",
        document_content=document_content
    )
    
    if result.get("error"):
        print(f"Error: {result['error']}")
        return
    
    processed_doc = result["processed_document"]
    
    # Inspect first page chunks
    first_page = processed_doc.pages[0]
    print(f"Page {first_page.page_number} has {len(first_page.chunks)} chunks:")
    
    for i, chunk in enumerate(first_page.chunks):
        print(f"\n--- Chunk {i} ---")
        print(f"Content preview: {chunk.page_content[:100]}...")
        print(f"Metadata: {chunk.metadata}")


if __name__ == "__main__":
    print("Document Processing Pipeline Examples\n")
    
    # Uncomment to run examples:
    # example_process_pdf()
    # example_process_word()
    # example_inspect_chunks()
    
    print("\nUncomment example functions in the script to run them.")
