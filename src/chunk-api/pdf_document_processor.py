"""
PDF document processor for chunking PDF files.
"""

from typing import List
import uuid
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from document_models import DocumentPage, ProcessedDocument


class PDFDocumentProcessor:
    """Advanced PDF processing that maintains page structure"""
    
    def __init__(self, chunk_size=250, chunk_overlap=25):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n",  " ", ""],
            is_separator_regex=False,
        )
    
    def process_pdf(
        self, 
        pdf_path: str, 
        location: str, 
        year: int, 
        doc_type: str, 
        document_name: str
    ) -> ProcessedDocument:
        """
        Process PDF and return structured page-based document chunks
        
        Args:
            pdf_path: Path to the PDF file
            location: Location/state associated with the document
            year: Year of the document
            doc_type: Type of document
            document_name: Name of the document
            
        Returns:
            ProcessedDocument with all pages and chunks
        """
        ship_to_text = "SHIP TO"
        invoice_to_text = "INVOICE TO"
        
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Process each page
        document_pages = []
        
        for page_num, page in enumerate(pages):
            # Clean text
            cleaned_text = self._clean_text(page.page_content)
            chunk_counter = 0

            # Skip nearly empty pages
            if len(cleaned_text.strip()) < 50:
                continue
            elif (ship_to_text in cleaned_text) or (invoice_to_text in cleaned_text):
                continue
            
            # Create chunks with enhanced metadata
            chunks = self.text_splitter.create_documents(
                texts=[cleaned_text],
                metadatas=[{
                    **page.metadata,
                    "page": page_num + 1,
                    "total_pages": len(pages),
                    "chunk_method": "smart_pdf_processor",
                    "char_count": len(cleaned_text),
                    "location": location,
                    "year": year,
                    "doc_type": doc_type,
                    "document_id": document_id,
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap
                }]
            )
            
            # Add chunk IDs to each document
            for doc in chunks:
                doc.metadata["document_id"] = f"{document_id}"
                doc.metadata["chunk_index"] = f"{chunk_counter}"
                chunk_counter += 1
            
            # Create DocumentPage for this page
            doc_page = DocumentPage(
                page_number=page_num + 1,
                chunks=chunks,
                content=cleaned_text
            )
            document_pages.append(doc_page)
        
        # Return ProcessedDocument
        return ProcessedDocument(
            document_id=document_id,
            document_name=document_name,
            total_pages=len(pages),
            pages=document_pages,
            year=year,
            location=location,
            doc_type=doc_type
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
        
        # Fix common PDF extraction issues
        text = text.replace("ﬁ", "fi")
        text = text.replace("ﬂ", "fl")
        
        return text
