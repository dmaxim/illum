"""
LangGraph-based document processing pipeline.

This pipeline orchestrates the entire document processing workflow:
1. Extract metadata from document
2. Route to appropriate processor (PDF or Word)
3. Process document into pages and chunks
4. Write results to blob storage
"""

import os
import tempfile
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph
from langgraph.constants import END

from models import DocumentMetadata
from document_models import ProcessedDocument
from pdf_document_processor import PDFDocumentProcessor
from word_document_processor import WordDocumentProcessor
from blob_storage_writer import BlobStorageWriter


class PipelineState(TypedDict):
    """State for the document processing pipeline."""
    # Input
    document_name: str
    file_name: str
    document_content: bytes
    location: Optional[str]
    year: Optional[int]
    doc_type: Optional[str]
    
    # Intermediate
    metadata: Optional[DocumentMetadata]
    temp_file_path: Optional[str]
    processor_type: Optional[Literal["pdf", "word"]]
    
    # Output
    processed_document: Optional[ProcessedDocument]
    blob_write_result: Optional[dict]
    error: Optional[str]


class DocumentProcessingPipeline:
    """LangGraph pipeline for processing documents."""
    
    def __init__(self):
        """Initialize the pipeline with processors and writer."""
        self.pdf_processor = PDFDocumentProcessor()
        self.word_processor = WordDocumentProcessor()
        self.blob_writer = BlobStorageWriter()
        self.graph = self._build_graph()
    
    def _extract_metadata(self, state: PipelineState) -> PipelineState:
        """
        Extract metadata from file name and determine file type.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with metadata
        """
        file_name = state["file_name"]
        document_name = state["document_name"]
        
        # Determine file extension from file_name
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # Use provided metadata or set defaults
        metadata = DocumentMetadata(
            document_name=document_name,
            file_extension=file_extension,
            location=state.get("location"),
            year=state.get("year"),
            doc_type=state.get("doc_type")
        )
        
        return {
            **state,
            "metadata": metadata
        }
    
    def _route_processor(self, state: PipelineState) -> PipelineState:
        """
        Determine which processor to use based on file extension.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with processor type
        """
        metadata = state["metadata"]
        file_extension = metadata.file_extension
        
        # Determine processor type
        if file_extension == ".pdf":
            processor_type = "pdf"
        elif file_extension in [".docx", ".doc"]:
            processor_type = "word"
        else:
            return {
                **state,
                "error": f"Unsupported file type: {file_extension}"
            }
        
        return {
            **state,
            "processor_type": processor_type
        }
    
    def _save_temp_file(self, state: PipelineState) -> PipelineState:
        """
        Save document content to temporary file for processing.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with temp file path
        """
        metadata = state["metadata"]
        content = state["document_content"]
        
        # Create temp file with appropriate extension
        suffix = metadata.file_extension
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        return {
            **state,
            "temp_file_path": temp_file_path
        }
    
    def _process_document(self, state: PipelineState) -> PipelineState:
        """
        Process document using the appropriate processor.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with processed document
        """
        processor_type = state["processor_type"]
        temp_file_path = state["temp_file_path"]
        metadata = state["metadata"]
        
        # Default metadata values
        location = metadata.location or "Unknown"
        year = metadata.year or 2024
        doc_type = metadata.doc_type or "general"
        document_name = metadata.document_name
        
        try:
            if processor_type == "pdf":
                processed_doc = self.pdf_processor.process_pdf(
                    pdf_path=temp_file_path,
                    location=location,
                    year=year,
                    doc_type=doc_type,
                    document_name=document_name
                )
            elif processor_type == "word":
                processed_doc = self.word_processor.process_document(
                    doc_path=temp_file_path,
                    location=location,
                    year=year,
                    doc_type=doc_type,
                    document_name=document_name
                )
            else:
                return {
                    **state,
                    "error": f"Unknown processor type: {processor_type}"
                }
            
            return {
                **state,
                "processed_document": processed_doc
            }
        except Exception as e:
            return {
                **state,
                "error": f"Error processing document: {str(e)}"
            }
        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def _write_to_blob(self, state: PipelineState) -> PipelineState:
        """
        Write processed document to blob storage.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with blob write results
        """
        processed_doc = state["processed_document"]
        
        try:
            write_result = self.blob_writer.write_processed_document(processed_doc)
            return {
                **state,
                "blob_write_result": write_result
            }
        except Exception as e:
            return {
                **state,
                "error": f"Error writing to blob storage: {str(e)}"
            }
    
    def _should_continue(self, state: PipelineState) -> str:
        """
        Determine if pipeline should continue or end.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Next node name or END
        """
        if state.get("error"):
            return END
        return "continue"
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine for document processing.
        
        Returns:
            Compiled StateGraph
        """
        # Create graph
        workflow = StateGraph(PipelineState)
        
        # Add nodes
        workflow.add_node("extract_metadata", self._extract_metadata)
        workflow.add_node("route_processor", self._route_processor)
        workflow.add_node("save_temp_file", self._save_temp_file)
        workflow.add_node("process_document", self._process_document)
        workflow.add_node("write_to_blob", self._write_to_blob)
        
        # Define edges
        workflow.set_entry_point("extract_metadata")
        workflow.add_edge("extract_metadata", "route_processor")
        
        # Conditional routing after route_processor
        workflow.add_conditional_edges(
            "route_processor",
            self._should_continue,
            {
                "continue": "save_temp_file",
                END: END
            }
        )
        
        workflow.add_edge("save_temp_file", "process_document")
        
        # Conditional routing after process_document
        workflow.add_conditional_edges(
            "process_document",
            self._should_continue,
            {
                "continue": "write_to_blob",
                END: END
            }
        )
        
        workflow.add_edge("write_to_blob", END)
        
        # Compile graph
        return workflow.compile()
    
    def process(
        self,
        document_name: str,
        file_name: str,
        document_content: bytes,
        location: Optional[str] = None,
        year: Optional[int] = None,
        doc_type: Optional[str] = None
    ) -> PipelineState:
        """
        Execute the document processing pipeline.
        
        Args:
            document_name: Name of the document for processing
            file_name: Name of the file (used for determining file type)
            document_content: Binary content of the document
            location: Optional location metadata
            year: Optional year metadata
            doc_type: Optional document type metadata
            
        Returns:
            Final pipeline state with results or errors
        """
        initial_state: PipelineState = {
            "document_name": document_name,
            "file_name": file_name,
            "document_content": document_content,
            "location": location,
            "year": year,
            "doc_type": doc_type,
            "metadata": None,
            "temp_file_path": None,
            "processor_type": None,
            "processed_document": None,
            "blob_write_result": None,
            "error": None
        }
        
        # Run the pipeline
        final_state = self.graph.invoke(initial_state)
        
        return final_state
