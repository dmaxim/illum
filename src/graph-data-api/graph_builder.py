"""
Knowledge graph builder classes for creating Neo4j graph structures.
Adapted from knowledge_graph.py and response_knowledge_graph.py.
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any
import logging

from models import EmbeddedChunkData

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Base class for building and managing knowledge graph in Neo4j"""
    
    def __init__(self, uri: str, username: str, password: str, database: str):
        """
        Initialize the GraphBuilder with Neo4j connection parameters
        
        Args:
            uri: Neo4j URI
            username: Neo4j username
            password: Neo4j password
            database: Neo4j database name
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
    
    def execute_query(self, cypher_query: str, parameters: dict = None):
        """
        Execute a Cypher query on the Neo4j database
        
        Args:
            cypher_query: The Cypher query string
            parameters: Optional dictionary of query parameters
        """
        try:
            with self.driver.session(database=self.database) as session:
                session.run(cypher_query, parameters)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise


class RequestGraphBuilder(GraphBuilder):
    """Class for building request document knowledge graphs"""
    
    def create_location_node(self, location_name: str):
        """Create a Location node in Neo4j"""
        logger.info(f"Creating location {location_name}")
        create_location_query = """
        MERGE (l:Location {name: $location_name})
        """
        parameters = {"location_name": location_name}
        self.execute_query(create_location_query, parameters)
    
    def create_year_node(self, year: int):
        """Create a Year node in Neo4j"""
        logger.info(f"Creating year {year}")
        create_year_query = """
        MERGE (y:Year {year: $year})
        """
        parameters = {"year": str(year)}
        self.execute_query(create_year_query, parameters)
    
    def create_rfp_year_node(self, rfp_year: str):
        """Create an RFP Year node in Neo4j"""
        logger.info(f"Creating RFP Year: {rfp_year}")
        create_rfp_year_query = """
        MERGE (r:Rfp {name: $rfp_year})
        """
        parameters = {"rfp_year": rfp_year}
        self.execute_query(create_rfp_year_query, parameters)
    
    def create_rfp_year_location_relationships(self, location_name: str, year: int, rfp_year: str):
        """Create relationships between Location, RFP, and Year nodes"""
        logger.info(f"Creating rfp year location association {location_name} to {year} to {rfp_year}")
        create_association_query = """
        MATCH (l:Location {name: $location_name})
        MATCH (r:Rfp {name: $rfp_year})
        MATCH (y:Year {year: $year})
        MERGE (l)-[:HAS_RFP]->(r)
        MERGE (r)-[:IS_YEAR]->(y)
        MERGE (r)-[:HAS_LOCATION]->(l)
        """
        parameters = {
            "location_name": location_name,
            "rfp_year": rfp_year,
            "year": str(year),
        }
        self.execute_query(create_association_query, parameters)
    
    def create_document_node(self, doc_name: str, source: str, doc_type: str, rfp_year: str):
        """Create a Document node and link it to an RFP"""
        logger.info(f"Creating document: {doc_name}")
        doc_create_query = """
        MERGE (w:Document {name: $doc_name, source: $doc_source, doc_type: $doc_type})
        """
        doc_parameters = {
            "doc_name": doc_name,
            "doc_source": source,
            "doc_type": doc_type
        }
        self.execute_query(doc_create_query, doc_parameters)
        
        # Create relationship between RFP and Document
        relationship_query = """
        MATCH (r:Rfp {name: $rfp_year})
        MATCH (d:Document {name: $doc_name})
        MERGE (r)-[:HAS_DOCUMENT]->(d)
        MERGE (d)-[:HAS_RFP]->(r)
        """
        relationship_parameters = {
            "rfp_year": rfp_year,
            "doc_name": doc_name
        }
        self.execute_query(relationship_query, relationship_parameters)
    
    def create_page_nodes(self, doc_name: str, chunks: List[EmbeddedChunkData]):
        """Create Page nodes based on chunks"""
        # Get unique pages from chunks
        pages_set = set(chunk.page_number for chunk in chunks)
        logger.info(f"Creating {len(pages_set)} page nodes for document: {doc_name}")
        
        for page_number in pages_set:
            # Get content for this page (combine all chunks for this page)
            page_chunks = [chunk for chunk in chunks if chunk.page_number == page_number]
            content = " ".join(chunk.content for chunk in page_chunks)
            
            # Create Page node
            create_page_query = """
            MERGE (p:Page {doc_name: $doc_name, page_number: $page_number})
            SET p.content = $content
            """
            page_parameters = {
                "doc_name": doc_name,
                "page_number": page_number,
                "content": content[:5000]  # Limit content size
            }
            self.execute_query(create_page_query, page_parameters)
            
            # Link Page to Document
            link_page_query = """
            MATCH (d:Document {name: $doc_name})
            MATCH (p:Page {doc_name: $doc_name, page_number: $page_number})
            MERGE (d)-[:HAS_PAGE]->(p)
            MERGE (p)-[:HAS_DOCUMENT]->(d)
            """
            link_parameters = {
                "doc_name": doc_name,
                "page_number": page_number
            }
            self.execute_query(link_page_query, link_parameters)
    
    def create_chunk_nodes(self, doc_name: str, chunks: List[EmbeddedChunkData]):
        """Create RequestChunk nodes for each embedded chunk"""
        logger.info(f"Creating {len(chunks)} chunk nodes for document: {doc_name}")
        
        for chunk in chunks:
            # Create RequestChunk node
            create_chunk_query = """
            MERGE (c:RequestChunk {chunk_id: $chunk_id})
            SET c.text = $text,
                c.embedding = $embedding,
                c.doc_name = $doc_name,
                c.page_number = $page_number,
                c.chunk_index = $chunk_index
            """
            chunk_parameters = {
                "chunk_id": chunk.chunk_id,
                "text": chunk.content,
                "embedding": chunk.embedding,
                "doc_name": doc_name,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index
            }
            self.execute_query(create_chunk_query, chunk_parameters)
            
            # Link Chunk to Page
            link_chunk_to_page_query = """
            MATCH (p:Page {doc_name: $doc_name, page_number: $page_number})
            MATCH (c:RequestChunk {chunk_id: $chunk_id})
            MERGE (p)-[:HAS_CHUNK]->(c)
            MERGE (c)-[:HAS_PAGE]->(p)
            """
            link_page_parameters = {
                "doc_name": doc_name,
                "page_number": chunk.page_number,
                "chunk_id": chunk.chunk_id
            }
            self.execute_query(link_chunk_to_page_query, link_page_parameters)
    
    def build_graph(self, document_id: str, chunks: List[EmbeddedChunkData]) -> int:
        """
        Build the knowledge graph from embedded chunks for a request document
        
        Args:
            document_id: The document identifier
            chunks: List of embedded chunk data
            
        Returns:
            Number of nodes created
        """
        if not chunks:
            raise ValueError("No chunks provided")
        
        # Extract metadata from first chunk
        first_chunk = chunks[0]
        location = first_chunk.metadata.location
        year = first_chunk.metadata.year
        doc_name = first_chunk.metadata.title or document_id
        doc_type = first_chunk.metadata.doc_type
        
        # Create RFP year identifier
        rfp_year = f"{location} RFP {str(year)[-2:]}" if location and year else f"RFP {document_id}"
        
        logger.info(f"Building graph for document: {doc_name}")
        logger.info(f"Location: {location}, Year: {year}, RFP Year: {rfp_year}")
        
        nodes_created = 0
        
        # Create Location node
        if location:
            self.create_location_node(location)
            nodes_created += 1
        
        # Create Year node
        if year:
            self.create_year_node(year)
            nodes_created += 1
        
        # Create RFP Year node
        self.create_rfp_year_node(rfp_year)
        nodes_created += 1
        
        # Create relationships between Location, RFP, and Year
        if location and year:
            self.create_rfp_year_location_relationships(location, year, rfp_year)
        
        # Create Document node and link to RFP
        source = f"{doc_name}.pdf"
        self.create_document_node(doc_name, source, doc_type, rfp_year)
        nodes_created += 1
        
        # Create Page nodes
        pages_set = set(chunk.page_number for chunk in chunks)
        self.create_page_nodes(doc_name, chunks)
        nodes_created += len(pages_set)
        
        # Create Chunk nodes
        self.create_chunk_nodes(doc_name, chunks)
        nodes_created += len(chunks)
        
        logger.info(f"Graph building complete for {doc_name}. Created {nodes_created} nodes")
        return nodes_created


class ResponseGraphBuilder(GraphBuilder):
    """Class for building response document knowledge graphs"""
    
    def create_document_node(self, doc_name: str, source: str, doc_type: str, rfp_name: str):
        """Create a Document node and link it to an RFP"""
        logger.info(f"Creating response document: {doc_name}")
        
        # Create Document node
        doc_create_query = """
        MERGE (d:Document {name: $doc_name, source: $doc_source, doc_type: $doc_type})
        """
        doc_parameters = {
            "doc_name": doc_name,
            "doc_source": source,
            "doc_type": doc_type
        }
        self.execute_query(doc_create_query, doc_parameters)
        
        # Create relationship between RFP and Document
        logger.info(f"Linking document to RFP: {rfp_name}")
        relationship_query = """
        MATCH (r:Rfp {name: $rfp_name})
        MATCH (d:Document {name: $doc_name})
        MERGE (r)-[:HAS_DOCUMENT]->(d)
        MERGE (d)-[:HAS_RFP]->(r)
        """
        relationship_parameters = {
            "rfp_name": rfp_name,
            "doc_name": doc_name
        }
        self.execute_query(relationship_query, relationship_parameters)
    
    def create_page_nodes(self, doc_name: str, chunks: List[EmbeddedChunkData]):
        """Create Page nodes based on chunks"""
        # Get unique pages from chunks
        pages_set = set(chunk.page_number for chunk in chunks)
        logger.info(f"Creating {len(pages_set)} Page nodes for document: {doc_name}")
        
        for page_number in pages_set:
            # Get content for this page
            page_chunks = [chunk for chunk in chunks if chunk.page_number == page_number]
            content = " ".join(chunk.content for chunk in page_chunks)
            
            # Create Page node
            create_page_query = """
            MERGE (p:Page {doc_name: $doc_name, page_number: $page_number})
            SET p.content = $content
            """
            page_parameters = {
                "doc_name": doc_name,
                "page_number": page_number,
                "content": content[:5000]  # Limit content size
            }
            self.execute_query(create_page_query, page_parameters)
            
            # Link Page to Document
            link_page_query = """
            MATCH (d:Document {name: $doc_name})
            MATCH (p:Page {doc_name: $doc_name, page_number: $page_number})
            MERGE (d)-[:HAS_PAGE]->(p)
            MERGE (p)-[:HAS_DOCUMENT]->(d)
            """
            link_parameters = {
                "doc_name": doc_name,
                "page_number": page_number
            }
            self.execute_query(link_page_query, link_parameters)
        
        logger.info(f"✓ Created {len(pages_set)} Page nodes and linked to document")
    
    def create_response_chunk_nodes(self, doc_name: str, chunks: List[EmbeddedChunkData]):
        """Create ResponseChunk nodes for each embedded chunk and link to pages"""
        logger.info(f"Creating {len(chunks)} ResponseChunk nodes for document: {doc_name}")
        
        for chunk in chunks:
            # Create ResponseChunk node
            create_chunk_query = """
            MERGE (c:ResponseChunk {chunk_id: $chunk_id})
            SET c.index = $chunk_index,
                c.text = $text,
                c.embedding = $embedding,
                c.doc_name = $doc_name,
                c.page_number = $page_number
            """
            chunk_parameters = {
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.content,
                "embedding": chunk.embedding,
                "doc_name": doc_name,
                "page_number": chunk.page_number
            }
            self.execute_query(create_chunk_query, chunk_parameters)
            
            # Link Chunk to Page
            link_chunk_to_page_query = """
            MATCH (p:Page {doc_name: $doc_name, page_number: $page_number})
            MATCH (c:ResponseChunk {chunk_id: $chunk_id})
            MERGE (p)-[:HAS_CHUNK]->(c)
            MERGE (c)-[:HAS_PAGE]->(p)
            """
            link_page_parameters = {
                "doc_name": doc_name,
                "page_number": chunk.page_number,
                "chunk_id": chunk.chunk_id
            }
            self.execute_query(link_chunk_to_page_query, link_page_parameters)
        
        logger.info(f"✓ Created {len(chunks)} ResponseChunk nodes and linked to pages")
    
    def build_graph(self, document_id: str, chunks: List[EmbeddedChunkData], rfp_name: str = None) -> int:
        """
        Build the knowledge graph from embedded chunks for a response document
        
        Args:
            document_id: The document identifier
            chunks: List of embedded chunk data
            rfp_name: Name of the RFP to link to (optional, will be derived from metadata if not provided)
            
        Returns:
            Number of nodes created
        """
        if not chunks:
            raise ValueError("No chunks provided")
        
        # Extract metadata from first chunk
        first_chunk = chunks[0]
        doc_name = first_chunk.metadata.title or document_id
        doc_type = first_chunk.metadata.doc_type
        source = first_chunk.metadata.source or f"{doc_name}.docx"
        
        # Derive RFP name if not provided
        if not rfp_name:
            location = first_chunk.metadata.location
            year = first_chunk.metadata.year
            if location and year:
                rfp_name = f"{location} RFP {str(year)[-2:]}"
            else:
                rfp_name = "Unknown RFP"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Building graph for response document: {doc_name}")
        logger.info(f"RFP: {rfp_name}")
        logger.info(f"{'='*60}\n")
        
        nodes_created = 0
        
        # Create Document node and link to RFP
        self.create_document_node(doc_name, source, doc_type, rfp_name)
        nodes_created += 1
        
        # Create Page nodes and link to Document
        pages_set = set(chunk.page_number for chunk in chunks)
        self.create_page_nodes(doc_name, chunks)
        nodes_created += len(pages_set)
        
        # Create ResponseChunk nodes and link to Pages
        self.create_response_chunk_nodes(doc_name, chunks)
        nodes_created += len(chunks)
        
        logger.info(f"\n✓ Graph building complete for {doc_name}. Created {nodes_created} nodes\n")
        return nodes_created
