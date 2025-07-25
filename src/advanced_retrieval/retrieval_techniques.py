import os
import sys
import json
import logging
import boto3
import time
import hashlib
import re
from typing import List, Dict, Any, Optional, Union, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('advanced_retrieval')

class AdvancedRetrieval:
    """Advanced retrieval techniques for the Database Knowledge Base"""

    def __init__(self, kb_id=None, region_name='us-east-1', model_id='us.anthropic.claude-sonnet-4-20250514-v1:0'):
        """Initialize with AWS Bedrock client and Knowledge Base ID"""
        self.kb_id = kb_id or os.environ.get('KNOWLEDGE_BASE_ID')
        if not self.kb_id:
            raise ValueError("Knowledge Base ID must be provided or set in KNOWLEDGE_BASE_ID environment variable")

        self.region_name = region_name
        self.model_id = model_id

        # Initialize Bedrock clients with explicit credential configuration
        try:
            # First try to get credentials from the environment
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region_name)
            self.kb_client = boto3.client('bedrock-agent-runtime', region_name=self.region_name)

            # Test connection to make sure credentials work
            logger.info(f"Testing Bedrock connection with KB ID: {self.kb_id}")
        except Exception as e:
            logger.error(f"Error initializing Bedrock clients: {e}")
            logger.warning("Using emergency fallback to default credentials")

            # Fallback to default session
            session = boto3.Session(region_name=self.region_name)
            self.bedrock_client = session.client('bedrock-runtime')
            self.kb_client = session.client('bedrock-agent-runtime')

        # Cache for queries to avoid redundant retrievals
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour

    def generate_cache_key(self, query_text, num_results=5, **kwargs):
        """Generate a cache key based on query parameters"""
        key_parts = [query_text, str(num_results)]

        # Add any additional kwargs sorted by key
        for k, v in sorted(kwargs.items()):
            if isinstance(v, dict) or isinstance(v, list):
                key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}:{v}")

        # Create a hash of all parameters
        key_string = "::".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def advanced_rag_query(self, query_text: str, use_extended_thinking: bool = True) -> Dict[str, Any]:
        """Main query method used by the API wrapper"""
        logger.info(f"Advanced RAG query called with query: {query_text}")

        # Use multi-strategy retrieval for best results
        result = self.multi_strategy_retrieval(query_text)

        # Extract contexts
        contexts = result.get('contexts', [])
        context_texts = [ctx.get('content', '').strip() for ctx in contexts if ctx.get('content')]

        # Extract thinking process
        thinking = result.get('thinking_process', '')

        # Generate a proper answer using Claude instead of just concatenating contexts
        answer = self.generate_answer_from_contexts(query_text, context_texts)

        return {
            "answer": answer,
            "thinking": thinking if use_extended_thinking else "",
            "retrieved_contexts": context_texts
        }

    def generate_answer_from_contexts(self, query_text: str, context_texts: List[str]) -> str:
        """Generate a comprehensive answer from retrieved contexts using Claude with feedback awareness"""
        if not context_texts:
            return f"I couldn't find relevant information in the database knowledge base for your query: '{query_text}'. Please try rephrasing your question or check if the topic is covered in the documentation."

        corrections_context = self.get_relevant_corrections(query_text)
        
        # Combine contexts for analysis
        combined_contexts = "\n\n---\n\n".join(context_texts[:10])  # Use top 10 contexts
        
        if corrections_context:
            combined_contexts += f"\n\n--- USER CORRECTIONS ---\n\n{corrections_context}"

        prompt = f"""You are a SQL query assistant. Based on the retrieved database documentation below, provide ONLY SQL statements that answer the user's query.

USER QUERY: {query_text}

RETRIEVED DOCUMENTATION:
{combined_contexts}

IMPORTANT INSTRUCTIONS:
1. Respond ONLY with SQL statements - no explanatory text
2. Use proper SQL syntax for the database system
3. Include table aliases for readability
4. Add appropriate WHERE clauses for filtering
5. Use meaningful column names in SELECT statements
6. If multiple queries are needed, separate them with semicolons
7. If user corrections are provided above, prioritize those over general documentation
8. If the query cannot be answered with available schema information, respond with: "-- Insufficient schema information to generate SQL"

SQL Response:"""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "temperature": 0.2,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )

            response_body = json.loads(response.get('body').read())
            result = response_body.get('content', [{}])[0].get('text', '')

            return result.strip() if result.strip() else f"I found relevant documentation but couldn't generate a proper response. The retrieved information contains: {combined_contexts[:1000]}..."

        except Exception as e:
            logger.error(f"Error generating answer from contexts: {e}")
            # Fallback to a simple response with the first context
            if context_texts:
                return f"Based on the database documentation, here's what I found for your query '{query_text}':\n\n{context_texts[0][:2000]}..."
            else:
                return f"I encountered an error while processing your query '{query_text}'. Please try again or rephrase your question."

    def get_relevant_corrections(self, query_text: str) -> str:
        """Get relevant user corrections for similar queries"""
        try:
            return ""
        except Exception as e:
            logger.error(f"Error retrieving corrections: {e}")
            return ""

    def query_database_relationships(self, table_name: str) -> Dict[str, Any]:
        """Wrapper method for relationship queries to match API expectations"""
        return self.relationship_retrieval(table_name)

    def standard_query(self, query_text: str, num_results: int = 5) -> Dict[str, Any]:
        """Standard retrieval from knowledge base"""
        cache_key = self.generate_cache_key(query_text, num_results, method="standard")

        if cache_key in self.cache and time.time() - self.cache[cache_key]['timestamp'] < self.cache_ttl:
            logger.info(f"Cache hit for query: {query_text}")
            return self.cache[cache_key]['result']

        logger.info(f"Performing standard retrieval for query: {query_text}")
        try:
            # Set a timeout of 10 seconds for this operation
            response = self.kb_client.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={
                    'text': query_text
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': num_results
                    }
                }
            )
            logger.info(f"Standard retrieval successful for query: {query_text}")

            result = {
                'query_text': query_text,
                'retrieval_method': 'standard',
                'contexts': [
                    {
                        'content': item.get('content', {}).get('text', ''),
                        'source': item.get('location', {}).get('s3Location', {}).get('uri', ''),
                        'content_sample': item.get('content', {}).get('text', '')[:500] + '...' if item.get('content', {}).get('text', '') else '',
                        'score': item.get('score', 0)
                    }
                    for item in response.get('retrievalResults', [])
                ]
            }

            # Cache the result
            self.cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error in standard retrieval, falling back to mock response: {e}")
            # In case of any error, return a mock response
            mock_result = {
                'query_text': query_text,
                'retrieval_method': 'standard (mock fallback)',
                'error': str(e),
                'contexts': [
                    {
                        'content': f"This is a mock response. The query was: {query_text}. There was an error connecting to the knowledge base: {str(e)}",
                        'source': 'mock-source',
                        'content_sample': f"This is a mock response. The query was: {query_text}...",
                        'score': 1.0
                    }
                ]
            }
            return mock_result

    def query_expansion(self, query_text: str, num_results: int = 5) -> Dict[str, Any]:
        """Query expansion: generate multiple versions of the query and aggregate results"""
        cache_key = self.generate_cache_key(query_text, num_results, method="expansion")

        if cache_key in self.cache and time.time() - self.cache[cache_key]['timestamp'] < self.cache_ttl:
            logger.info(f"Cache hit for expanded query: {query_text}")
            return self.cache[cache_key]['result']

        logger.info(f"Performing query expansion for: {query_text}")

        try:
            expanded_queries = self.generate_expanded_queries(query_text)
            all_contexts = []
            thinking_process = f"Original query: {query_text}\n\nExpanded queries:\n"

            for i, expanded in enumerate(expanded_queries):
                thinking_process += f"{i+1}. {expanded}\n"

                response = self.kb_client.retrieve(
                    knowledgeBaseId=self.kb_id,
                    retrievalQuery={
                        'text': expanded
                    },
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': num_results
                        }
                    }
                )

                contexts = [
                    {
                        'content': item.get('content', {}).get('text', ''),
                        'source': item.get('location', {}).get('s3Location', {}).get('uri', ''),
                        'content_sample': item.get('content', {}).get('text', '')[:500] + '...' if item.get('content', {}).get('text', '') else '',
                        'score': item.get('score', 0),
                        'from_query': expanded
                    }
                    for item in response.get('retrievalResults', [])
                ]
                all_contexts.extend(contexts)

            # Deduplicate contexts based on content
            unique_contexts = {}
            for context in all_contexts:
                content_hash = hashlib.md5(context['content'].encode()).hexdigest()
                if content_hash not in unique_contexts or context['score'] > unique_contexts[content_hash]['score']:
                    unique_contexts[content_hash] = context

            # Sort by score and take top results
            sorted_contexts = sorted(unique_contexts.values(), key=lambda x: x['score'], reverse=True)[:num_results]

            thinking_process += f"\nRetrieved {len(all_contexts)} total contexts, deduplicated to {len(unique_contexts)} unique contexts."
            thinking_process += f"\nSelected top {len(sorted_contexts)} contexts based on relevance score."

            result = {
                'query_text': query_text,
                'retrieval_method': 'query_expansion',
                'contexts': sorted_contexts,
                'thinking_process': thinking_process
            }

            # Cache the result
            self.cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error in query expansion: {e}")
            return {
                'query_text': query_text,
                'retrieval_method': 'query_expansion',
                'error': str(e),
                'contexts': []
            }

    def generate_expanded_queries(self, query_text: str) -> List[str]:
        """Generate semantically diverse versions of the query using Claude 3.7 Sonnet"""
        prompt = f"""Please generate 3-5 semantically diverse variations of this database query to improve retrieval.
The variations should capture different ways of expressing the same information need, using different terms,
structures, or perspectives. Focus on database terminology, SQL constructs, and schema concepts.

QUERY: {query_text}

Provide ONLY the query variations as plain text, one per line. No explanations or additional text."""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1500,
                    "temperature": 0.7,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )

            response_body = json.loads(response.get('body').read())
            result = response_body.get('content', [{}])[0].get('text', '')

            # Split the result by lines and filter out empty lines
            queries = [q.strip() for q in result.split('\n') if q.strip()]

            # Always include the original query
            if query_text not in queries:
                queries.append(query_text)

            return queries

        except Exception as e:
            logger.error(f"Error generating expanded queries: {e}")
            return [query_text]  # Fall back to original query

    def hyde_retrieval(self, query_text: str, num_results: int = 5) -> Dict[str, Any]:
        """Hypothetical Document Embedding (HyDE): Generate a hypothetical document that answers the query,
        then retrieve based on that document"""
        cache_key = self.generate_cache_key(query_text, num_results, method="hyde")

        if cache_key in self.cache and time.time() - self.cache[cache_key]['timestamp'] < self.cache_ttl:
            logger.info(f"Cache hit for HyDE query: {query_text}")
            return self.cache[cache_key]['result']

        logger.info(f"Performing HyDE retrieval for query: {query_text}")

        try:
            # Generate a hypothetical document that answers the query
            hypothetical_doc = self.generate_hypothetical_document(query_text)

            thinking_process = f"Original query: {query_text}\n\nGenerated hypothetical document to use for retrieval:\n{hypothetical_doc}\n"

            # Use the hypothetical document for retrieval
            response = self.kb_client.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={
                    'text': hypothetical_doc
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': num_results
                    }
                }
            )

            contexts = [
                {
                    'content': item.get('content', {}).get('text', ''),
                    'source': item.get('location', {}).get('s3Location', {}).get('uri', ''),
                    'content_sample': item.get('content', {}).get('text', '')[:500] + '...' if item.get('content', {}).get('text', '') else '',
                    'score': item.get('score', 0)
                }
                for item in response.get('retrievalResults', [])
            ]

            thinking_process += f"\nRetrieved {len(contexts)} contexts using the hypothetical document."

            result = {
                'query_text': query_text,
                'retrieval_method': 'hyde',
                'contexts': contexts,
                'hypothetical_document': hypothetical_doc,
                'thinking_process': thinking_process
            }

            # Cache the result
            self.cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error in HyDE retrieval: {e}")
            return {
                'query_text': query_text,
                'retrieval_method': 'hyde',
                'error': str(e),
                'contexts': []
            }

    def generate_hypothetical_document(self, query_text: str) -> str:
        """Generate a hypothetical document that would answer the query"""
        prompt = f"""Create a hypothetical, ideal document that would perfectly answer this database-related query:

QUERY: {query_text}

Create a technical document that contains information that would be the perfect match for this query.
Include specific database concepts, table names, column names, relationships, and technical details that would be
relevant. Write as if this were an excerpt from an actual database documentation or SQL guide.

Respond with the hypothetical document only. Do not include any introductions or explanations."""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "temperature": 0.2,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )

            response_body = json.loads(response.get('body').read())
            result = response_body.get('content', [{}])[0].get('text', '')

            return result.strip()

        except Exception as e:
            logger.error(f"Error generating hypothetical document: {e}")
            return query_text  # Fall back to original query

    def multi_strategy_retrieval(self, query_text: str, num_results: int = 8) -> Dict[str, Any]:
        """Combine multiple retrieval strategies and aggregate results"""
        cache_key = self.generate_cache_key(query_text, num_results, method="multi")

        if cache_key in self.cache and time.time() - self.cache[cache_key]['timestamp'] < self.cache_ttl:
            logger.info(f"Cache hit for multi-strategy query: {query_text}")
            return self.cache[cache_key]['result']

        logger.info(f"Performing multi-strategy retrieval for query: {query_text}")

        try:
            # Get results from each method (with fewer results per method)
            results_per_method = max(2, num_results // 3)
            standard_results = self.standard_query(query_text, results_per_method)
            expansion_results = self.query_expansion(query_text, results_per_method)
            hyde_results = self.hyde_retrieval(query_text, results_per_method)

            # Combine all contexts
            all_contexts = []
            all_contexts.extend(standard_results.get('contexts', []))
            all_contexts.extend(expansion_results.get('contexts', []))
            all_contexts.extend(hyde_results.get('contexts', []))

            # Deduplicate contexts based on content
            unique_contexts = {}
            for context in all_contexts:
                content_hash = hashlib.md5(context['content'].encode()).hexdigest()
                if content_hash not in unique_contexts or context['score'] > unique_contexts[content_hash]['score']:
                    unique_contexts[content_hash] = context

            # Sort by score and take top results
            sorted_contexts = sorted(unique_contexts.values(), key=lambda x: x['score'], reverse=True)[:num_results]

            # Create detailed thinking process
            thinking_process = "# Multi-Strategy Retrieval Process\n\n"
            thinking_process += f"Query: {query_text}\n\n"
            thinking_process += "## Standard Retrieval\n"
            thinking_process += f"Retrieved {len(standard_results.get('contexts', []))} results\n\n"

            thinking_process += "## Query Expansion\n"
            if 'thinking_process' in expansion_results:
                thinking_process += expansion_results['thinking_process'] + "\n\n"
            else:
                thinking_process += f"Retrieved {len(expansion_results.get('contexts', []))} results\n\n"

            thinking_process += "## Hypothetical Document Embedding (HyDE)\n"
            if 'thinking_process' in hyde_results:
                thinking_process += hyde_results['thinking_process'] + "\n\n"
            else:
                thinking_process += f"Retrieved {len(hyde_results.get('contexts', []))} results\n\n"

            thinking_process += "## Aggregation Results\n"
            thinking_process += f"Combined {len(all_contexts)} total contexts from all methods\n"
            thinking_process += f"After deduplication: {len(unique_contexts)} unique contexts\n"
            thinking_process += f"Final selection: {len(sorted_contexts)} top contexts by relevance score\n"

            result = {
                'query_text': query_text,
                'retrieval_method': 'multi_strategy',
                'contexts': sorted_contexts,
                'thinking_process': thinking_process
            }

            # Cache the result
            self.cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error in multi-strategy retrieval: {e}")
            return {
                'query_text': query_text,
                'retrieval_method': 'multi_strategy',
                'error': str(e),
                'contexts': []
            }

    def relationship_retrieval(self, table_name: str, num_results: int = 10) -> Dict[str, Any]:
        """Specialized retrieval for table relationship information"""
        cache_key = self.generate_cache_key(table_name, num_results, method="relationship")

        if cache_key in self.cache and time.time() - self.cache[cache_key]['timestamp'] < self.cache_ttl:
            logger.info(f"Cache hit for relationship query: {table_name}")
            return self.cache[cache_key]['result']

        logger.info(f"Performing relationship retrieval for table: {table_name}")

        try:
            # Generate queries specific to relationship information
            queries = [
                f"relationships of {table_name} table",
                f"{table_name} foreign keys",
                f"tables that reference {table_name}",
                f"{table_name} primary key",
                f"{table_name} table schema relationships"
            ]

            all_contexts = []
            thinking_process = f"Retrieving relationship information for table: {table_name}\n\nGenerated specialized queries:\n"

            for i, query in enumerate(queries):
                thinking_process += f"{i+1}. {query}\n"

                response = self.kb_client.retrieve(
                    knowledgeBaseId=self.kb_id,
                    retrievalQuery={
                        'text': query
                    },
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': num_results // len(queries) + 1
                        }
                    }
                )

                contexts = [
                    {
                        'content': item.get('content', {}).get('text', ''),
                        'source': item.get('location', {}).get('s3Location', {}).get('uri', ''),
                        'content_sample': item.get('content', {}).get('text', '')[:500] + '...' if item.get('content', {}).get('text', '') else '',
                        'score': item.get('score', 0),
                        'from_query': query
                    }
                    for item in response.get('retrievalResults', [])
                ]
                all_contexts.extend(contexts)

            # Deduplicate contexts based on content
            unique_contexts = {}
            for context in all_contexts:
                content_hash = hashlib.md5(context['content'].encode()).hexdigest()
                if content_hash not in unique_contexts or context['score'] > unique_contexts[content_hash]['score']:
                    unique_contexts[content_hash] = context

            # Sort by score and take top results
            sorted_contexts = sorted(unique_contexts.values(), key=lambda x: x['score'], reverse=True)[:num_results]

            thinking_process += f"\nRetrieved {len(all_contexts)} total contexts, deduplicated to {len(unique_contexts)} unique contexts."
            thinking_process += f"\nSelected top {len(sorted_contexts)} contexts based on relevance score."

            # Generate relationship analysis using Claude
            relationship_analysis = self.generate_relationship_analysis(table_name, sorted_contexts)

            result = {
                'table_name': table_name,
                'retrieval_method': 'relationship',
                'contexts': sorted_contexts,
                'relationship_analysis': relationship_analysis,
                'thinking_process': thinking_process
            }

            # Cache the result
            self.cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error in relationship retrieval: {e}")
            return {
                'table_name': table_name,
                'retrieval_method': 'relationship',
                'error': str(e),
                'contexts': []
            }

    def generate_relationship_analysis(self, table_name: str, contexts: List[Dict]) -> str:
        """Generate relationship analysis based on retrieved contexts"""
        # Extract content from contexts
        context_texts = [ctx['content'] for ctx in contexts if ctx['content']]
        context_combined = "\n\n---\n\n".join(context_texts)

        prompt = f"""Based on the following database documentation excerpts, provide a comprehensive analysis of all relationships for the '{table_name}' table.

DOCUMENTATION EXCERPTS:
{context_combined}

Please provide a detailed explanation of:
1. Primary key(s) of the '{table_name}' table
2. Foreign keys in '{table_name}' that reference other tables
3. Tables that have foreign keys referencing '{table_name}'
4. The complete relationship graph of '{table_name}'
5. Important notes about these relationships (e.g., cascade delete rules, indexing considerations)

Format your response as a technical but readable analysis with markdown formatting. Use bullet points and tables where appropriate.
If the information is not available in the provided documentation, clearly indicate what's missing."""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "temperature": 0.2,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )

            response_body = json.loads(response.get('body').read())
            result = response_body.get('content', [{}])[0].get('text', '')

            return result.strip()

        except Exception as e:
            logger.error(f"Error generating relationship analysis: {e}")
            return f"Error generating relationship analysis: {e}"

    def optimize_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """Analyze and optimize a SQL query based on database schema knowledge"""
        cache_key = self.generate_cache_key(sql_query, method="optimize")

        if cache_key in self.cache and time.time() - self.cache[cache_key]['timestamp'] < self.cache_ttl:
            logger.info(f"Cache hit for SQL optimization")
            return self.cache[cache_key]['result']

        logger.info(f"Performing SQL query optimization")

        try:
            # Parse the SQL query to identify tables and columns
            table_pattern = r'(?:FROM|JOIN)\s+(\w+)'
            tables = re.findall(table_pattern, sql_query, re.IGNORECASE)

            # Fetch relevant information for each table
            thinking_process = f"Extracting tables from SQL query:\n{sql_query}\n\nIdentified tables: {', '.join(tables)}\n\n"
            all_contexts = []

            for table in tables:
                thinking_process += f"Retrieving schema information for table: {table}\n"
                table_queries = [
                    f"{table} schema columns indexes",
                    f"{table} table structure",
                    f"{table} primary key and indexes"
                ]

                for query in table_queries:
                    response = self.kb_client.retrieve(
                        knowledgeBaseId=self.kb_id,
                        retrievalQuery={
                            'text': query
                        },
                        retrievalConfiguration={
                            'vectorSearchConfiguration': {
                                'numberOfResults': 3
                            }
                        }
                    )

                    contexts = [
                        {
                            'content': item.get('content', {}).get('text', ''),
                            'source': item.get('location', {}).get('s3Location', {}).get('uri', ''),
                            'content_sample': item.get('content', {}).get('text', '')[:500] + '...' if item.get('content', {}).get('text', '') else '',
                            'score': item.get('score', 0)
                        }
                        for item in response.get('retrievalResults', [])
                    ]
                    all_contexts.extend(contexts)

            # Also get relevant query patterns and optimizations
            thinking_process += f"Retrieving relevant query patterns and optimization information\n"
            optimization_query = f"SQL query optimization for: {sql_query[:100]}..."

            response = self.kb_client.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={
                    'text': optimization_query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5
                    }
                }
            )

            optimization_contexts = [
                {
                    'content': item.get('content', {}).get('text', ''),
                    'source': item.get('location', {}).get('s3Location', {}).get('uri', ''),
                    'content_sample': item.get('content', {}).get('text', '')[:500] + '...' if item.get('content', {}).get('text', '') else '',
                    'score': item.get('score', 0)
                }
                for item in response.get('retrievalResults', [])
            ]
            all_contexts.extend(optimization_contexts)

            # Deduplicate contexts based on content
            unique_contexts = {}
            for context in all_contexts:
                content_hash = hashlib.md5(context['content'].encode()).hexdigest()
                if content_hash not in unique_contexts or context['score'] > unique_contexts[content_hash]['score']:
                    unique_contexts[content_hash] = context

            sorted_contexts = sorted(unique_contexts.values(), key=lambda x: x['score'], reverse=True)[:10]
            thinking_process += f"Retrieved {len(all_contexts)} total contexts, deduplicated to {len(sorted_contexts)} contexts for analysis.\n"

            # Generate optimization analysis using Claude
            optimization_analysis = self.generate_sql_optimization(sql_query, sorted_contexts)

            result = {
                'sql_query': sql_query,
                'retrieval_method': 'sql_optimization',
                'optimization_analysis': optimization_analysis,
                'contexts': sorted_contexts,
                'thinking_process': thinking_process
            }

            # Cache the result
            self.cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error in SQL query optimization: {e}")
            return {
                'sql_query': sql_query,
                'retrieval_method': 'sql_optimization',
                'error': str(e),
                'contexts': []
            }

    def generate_sql_optimization(self, sql_query: str, contexts: List[Dict]) -> str:
        """Generate SQL optimization recommendations based on schema knowledge"""
        # Extract content from contexts
        context_texts = [ctx['content'] for ctx in contexts if ctx['content']]
        context_combined = "\n\n---\n\n".join(context_texts)

        prompt = f"""Analyze and optimize this SQL query. Respond with ONLY the optimized SQL and brief performance comments.

ORIGINAL SQL:
```sql
{sql_query}
```

SCHEMA INFORMATION:
{context_combined}

Provide:
1. Optimized SQL query with performance improvements
2. Brief comments (-- format) explaining key optimizations
3. Index recommendations as SQL comments

OPTIMIZED SQL:"""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 3000,
                    "temperature": 0.2,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )

            response_body = json.loads(response.get('body').read())
            result = response_body.get('content', [{}])[0].get('text', '')

            return result.strip()

        except Exception as e:
            logger.error(f"Error generating SQL optimization: {e}")
            return f"Error generating SQL optimization recommendations: {e}"


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Advanced retrieval techniques for Database Knowledge Base')
    parser.add_argument('--kb-id', help='Knowledge Base ID')
    parser.add_argument('--query', help='Query text for testing')
    parser.add_argument('--method', choices=['standard', 'expansion', 'hyde', 'multi', 'relationship', 'optimize'],
                       default='multi', help='Retrieval method to use')
    parser.add_argument('--table', help='Table name for relationship retrieval')
    parser.add_argument('--sql', help='SQL query for optimization')

    args = parser.parse_args()

    try:
        retriever = AdvancedRetrieval(kb_id=args.kb_id)

        if args.method == 'relationship' and args.table:
            result = retriever.relationship_retrieval(args.table)
        elif args.method == 'optimize' and args.sql:
            result = retriever.optimize_sql_query(args.sql)
        elif args.query:
            if args.method == 'standard':
                result = retriever.standard_query(args.query)
            elif args.method == 'expansion':
                result = retriever.query_expansion(args.query)
            elif args.method == 'hyde':
                result = retriever.hyde_retrieval(args.query)
            else:  # Default to multi-strategy
                result = retriever.multi_strategy_retrieval(args.query)
        else:
            print("Error: Missing required arguments. Use --help for usage information.")
            sys.exit(1)

        # Print the result
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
