#!/usr/bin/env python3
"""
Retrieval utilities for the Database Knowledge Base application
Handles connection to Amazon Bedrock Knowledge Base
"""

import os
import json
import logging
import sys
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('retrieval_utils')

def validate_request(event):
    """Validate incoming request and extract body"""
    try:
        if isinstance(event, dict) and 'body' in event:
            # AWS Lambda event format
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            # Direct dictionary (FastAPI format)
            body = event
        
        return True, body
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Invalid request format: {e}")
        return False, "Invalid JSON in request body"

def format_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format response for API Gateway or FastAPI"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body)
    }

def get_retrieval_client(kb_id: Optional[str] = None):
    """Get the retrieval client instance for a specific or default knowledge base"""
    try:
        # Try to import the advanced retrieval module
        from src.advanced_retrieval.retrieval_techniques import AdvancedRetrieval
        
        # Use provided KB ID or fall back to environment variable
        knowledge_base_id = kb_id or os.getenv('KNOWLEDGE_BASE_ID', 'KRD3MW7QFS')
        region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        logger.info(f"Initializing AdvancedRetrieval with KB ID: {knowledge_base_id}")
        retrieval_client = AdvancedRetrieval(
            kb_id=knowledge_base_id,
            region_name=region
        )
        
        return retrieval_client
        
    except ImportError as e:
        logger.error(f"Could not import AdvancedRetrieval: {e}")
        # Return a mock client for testing
        return MockRetrievalClient(kb_id)
    except Exception as e:
        logger.error(f"Error initializing retrieval client: {e}")
        # Return a mock client for testing
        return MockRetrievalClient(kb_id)

def create_retrieval_client(kb_id: str, region: str = None):
    """Create a new retrieval client for a specific knowledge base ID"""
    try:
        from src.advanced_retrieval.retrieval_techniques import AdvancedRetrieval
        
        region = region or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        logger.info(f"Creating new AdvancedRetrieval client for KB ID: {kb_id}")
        retrieval_client = AdvancedRetrieval(
            kb_id=kb_id,
            region_name=region
        )
        
        return retrieval_client
        
    except ImportError as e:
        logger.error(f"Could not import AdvancedRetrieval: {e}")
        return MockRetrievalClient(kb_id)
    except Exception as e:
        logger.error(f"Error creating retrieval client for KB {kb_id}: {e}")
        return MockRetrievalClient(kb_id)

class MockRetrievalClient:
    """Mock retrieval client for testing when Bedrock is not available"""
    
    def __init__(self, kb_id: Optional[str] = None):
        self.kb_id = kb_id or 'mock-kb-id'
        logger.warning(f"Using MockRetrievalClient for KB {self.kb_id} - Bedrock not available")
    
    def advanced_rag_query(self, query_text: str, use_extended_thinking: bool = True) -> Dict[str, Any]:
        """Mock implementation of advanced RAG query"""
        logger.info(f"Mock query for KB {self.kb_id}: {query_text}")
        
        return {
            'answer': f"Mock response from KB {self.kb_id} for query: '{query_text}'. This is a test response because the Knowledge Base connection is not available. Please check your AWS credentials and Knowledge Base configuration.",
            'thinking': f"This is a mock thinking process for KB {self.kb_id} because the real Bedrock Knowledge Base is not accessible.",
            'retrieved_contexts': [
                f"Mock context 1 from KB {self.kb_id}: Database schema information would appear here",
                f"Mock context 2 from KB {self.kb_id}: Query examples would appear here",
                f"Mock context 3 from KB {self.kb_id}: Relationship information would appear here"
            ]
        }
    
    def query_database_relationships(self, table_name: str) -> Dict[str, Any]:
        """Mock implementation of relationship query"""
        logger.info(f"Mock relationship query for table: {table_name}")
        
        return {
            'table_name': table_name,
            'relationship_analysis': f"Mock relationship analysis for table '{table_name}'. This table would have foreign key relationships, indexes, and constraints that would be described here if the Knowledge Base was connected.",
            'thinking_process': "Mock thinking process for relationship analysis.",
            'retrieved_contexts': [
                f"Mock context about {table_name} relationships",
                f"Mock context about {table_name} constraints"
            ]
        }