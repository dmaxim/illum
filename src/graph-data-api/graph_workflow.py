"""
LangGraph workflow for building knowledge graphs from document chunks.
Routes documents based on doc_type (request vs response) and processes accordingly.
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
import logging

from models import GraphState, EmbeddedChunkData
from graph_builder import RequestGraphBuilder, ResponseGraphBuilder

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State definition for the workflow"""
    document_id: str
    doc_type: str
    location: str
    year: int
    chunks: list
    nodes_created: int
    error: str
    neo4j_config: dict


def determine_document_type(state: WorkflowState) -> WorkflowState:
    """
    First node: Determine the document type from the chunks metadata.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with doc_type determined
    """
    logger.info("Step 1: Determining document type")
    
    try:
        chunks = state["chunks"]
        if not chunks:
            state["error"] = "No chunks provided"
            return state
        
        # Get doc_type from first chunk's metadata
        first_chunk = chunks[0]
        doc_type = first_chunk.metadata.doc_type
        
        if not doc_type:
            state["error"] = "doc_type not found in chunk metadata"
            return state
        
        state["doc_type"] = doc_type
        
        # Also extract location and year for potential use
        state["location"] = first_chunk.metadata.location
        state["year"] = first_chunk.metadata.year
        
        logger.info(f"Determined document type: {doc_type}")
        
    except Exception as e:
        logger.error(f"Error determining document type: {e}")
        state["error"] = str(e)
    
    return state


def route_by_document_type(state: WorkflowState) -> str:
    """
    Conditional edge: Route to appropriate builder based on doc_type.
    
    Args:
        state: Current workflow state
        
    Returns:
        Name of the next node to execute
    """
    if state.get("error"):
        logger.error(f"Error in workflow, ending: {state['error']}")
        return "end"
    
    doc_type = state.get("doc_type", "").lower()
    
    if doc_type == "request":
        logger.info("Routing to request graph builder")
        return "build_request_graph"
    elif doc_type == "response":
        logger.info("Routing to response graph builder")
        return "build_response_graph"
    else:
        logger.warning(f"Unknown doc_type '{doc_type}', defaulting to request")
        return "build_request_graph"


def build_request_graph(state: WorkflowState) -> WorkflowState:
    """
    Build knowledge graph for request documents.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with nodes_created count
    """
    logger.info("Step 2: Building request document graph")
    
    try:
        neo4j_config = state["neo4j_config"]
        builder = RequestGraphBuilder(
            uri=neo4j_config["uri"],
            username=neo4j_config["username"],
            password=neo4j_config["password"],
            database=neo4j_config["database"]
        )
        
        try:
            nodes_created = builder.build_graph(
                document_id=state["document_id"],
                chunks=state["chunks"]
            )
            state["nodes_created"] = nodes_created
            logger.info(f"Successfully created {nodes_created} nodes for request document")
        finally:
            builder.close()
            
    except Exception as e:
        logger.error(f"Error building request graph: {e}")
        state["error"] = str(e)
    
    return state


def build_response_graph(state: WorkflowState) -> WorkflowState:
    """
    Build knowledge graph for response documents.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with nodes_created count
    """
    logger.info("Step 2: Building response document graph")
    
    try:
        neo4j_config = state["neo4j_config"]
        builder = ResponseGraphBuilder(
            uri=neo4j_config["uri"],
            username=neo4j_config["username"],
            password=neo4j_config["password"],
            database=neo4j_config["database"]
        )
        
        try:
            # Derive RFP name from metadata if available
            rfp_name = None
            if state.get("location") and state.get("year"):
                rfp_name = f"{state['location']} RFP {str(state['year'])[-2:]}"
            
            nodes_created = builder.build_graph(
                document_id=state["document_id"],
                chunks=state["chunks"],
                rfp_name=rfp_name
            )
            state["nodes_created"] = nodes_created
            logger.info(f"Successfully created {nodes_created} nodes for response document")
        finally:
            builder.close()
            
    except Exception as e:
        logger.error(f"Error building response graph: {e}")
        state["error"] = str(e)
    
    return state


def create_graph_workflow():
    """
    Create and compile the LangGraph workflow for building knowledge graphs.
    
    Returns:
        Compiled workflow graph
    """
    # Create the graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("determine_type", determine_document_type)
    workflow.add_node("build_request_graph", build_request_graph)
    workflow.add_node("build_response_graph", build_response_graph)
    
    # Set entry point
    workflow.set_entry_point("determine_type")
    
    # Add conditional edges from determine_type
    workflow.add_conditional_edges(
        "determine_type",
        route_by_document_type,
        {
            "build_request_graph": "build_request_graph",
            "build_response_graph": "build_response_graph",
            "end": END
        }
    )
    
    # Add edges from builders to END
    workflow.add_edge("build_request_graph", END)
    workflow.add_edge("build_response_graph", END)
    
    # Compile the graph
    app = workflow.compile()
    
    logger.info("Graph workflow created and compiled")
    return app


def process_document_chunks(
    document_id: str,
    chunks: list,
    neo4j_config: dict
) -> Dict[str, Any]:
    """
    Process document chunks through the LangGraph workflow.
    
    Args:
        document_id: Document identifier
        chunks: List of EmbeddedChunkData objects
        neo4j_config: Neo4j configuration dictionary
        
    Returns:
        Dictionary with processing results
    """
    logger.info(f"Processing document {document_id} with {len(chunks)} chunks")
    
    # Create workflow
    app = create_graph_workflow()
    
    # Initialize state
    initial_state: WorkflowState = {
        "document_id": document_id,
        "doc_type": "",
        "location": None,
        "year": None,
        "chunks": chunks,
        "nodes_created": 0,
        "error": None,
        "neo4j_config": neo4j_config
    }
    
    # Run workflow
    final_state = app.invoke(initial_state)
    
    # Return results
    return {
        "document_id": final_state["document_id"],
        "doc_type": final_state["doc_type"],
        "total_chunks": len(chunks),
        "nodes_created": final_state["nodes_created"],
        "error": final_state.get("error")
    }
