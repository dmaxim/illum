"""
Word document processor for chunking Word documents.
"""

from typing import List
import uuid
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from document_models import DocumentPage, ProcessedDocument


class WordDocumentProcessor:
    """Advanced Word Document processing with smart chunking"""
    
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        """
        Initialize the Word Document Processor
        
        Args:
            chunk_size: Size of text chunks (default: 1000)
            chunk_overlap: Overlap between chunks (default: 100)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
    
    def process_document(
        self, 
        doc_path: str, 
        location: str, 
        year: int, 
        doc_type: str,
        document_name: str
    ) -> ProcessedDocument:
        """
        Process Word Document with page-based chunking and metadata enhancement
        
        Args:
            doc_path: Path to the Word document
            location: Location/state associated with the document
            year: Year of the document
            doc_type: Type of document (e.g., "verida-response")
            document_name: Name of the document
            
        Returns:
            ProcessedDocument with all pages and chunks
        """
        # Load Word doc using Unstructured loader in paged mode
        print(f"Loading Word document: {doc_path}")
        doc_loader = UnstructuredWordDocumentLoader(doc_path, mode="paged")
        doc_pages = doc_loader.load()
        
        print(f"Loaded {len(doc_pages)} document pages")
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Process each page
        document_pages = []
        chunk_counter = 0
        
        for page_num, page_doc in enumerate(doc_pages):
            # Clean text
            cleaned_text = self._clean_text(page_doc.page_content)
            
            # Skip nearly empty pages
            if len(cleaned_text.strip()) < 50:
                continue
            
            # Create chunks for this page with enhanced metadata
            chunks = self.text_splitter.create_documents(
                texts=[cleaned_text],
                metadatas=[{
                    **page_doc.metadata,
                    "page": page_num + 1,
                    "page_number": page_num + 1,
                    "total_pages": len(doc_pages),
                    "chunk_method": "smart_word_doc_processor",
                    "char_count": len(cleaned_text),
                    "location": location,
                    "year": year,
                    "doc_type": doc_type,
                    "document_id": document_id,
                    "document_name": document_name,
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap
                }]
            )
            
            # Add chunk IDs to each chunk for this page
            for chunk in chunks:
                chunk.metadata["document_id"] = document_id
                chunk.metadata["chunk_id"] = f"{document_id}_{chunk_counter}"
                chunk.metadata["chunk_index"] = chunk_counter
                chunk_counter += 1
            
            # Create DocumentPage for this page
            doc_page = DocumentPage(
                page_number=page_num + 1,
                content=cleaned_text,
                chunks=chunks
            )
            document_pages.append(doc_page)
        
        print(f"Processed into {len(document_pages)} pages with {chunk_counter} total chunks")
        
        # Return ProcessedDocument
        return ProcessedDocument(
            document_id=document_id,
            document_name=document_name,
            year=year,
            location=location,
            doc_type=doc_type,
            total_pages=len(doc_pages),
            pages=document_pages
        )
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        return text
