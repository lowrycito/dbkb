import os
import logging
import boto3
import json
import time
from botocore.exceptions import ClientError

PARENT_CHUNK_MAX_TOKENS = 4000  # Complete table definitions with relationships
CHILD_CHUNK_MAX_TOKENS = 800    # Specific queries and column details  
CHUNK_OVERLAP_TOKENS = 150      # Maintain foreign key relationships across chunks

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bedrock_kb_setup')

class BedrockKnowledgeBaseSetup:
    """Class to handle Amazon Bedrock Knowledge Base creation and configuration"""

    def __init__(self, region_name='us-east-1'):
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=region_name)
        self.bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime', region_name=region_name)
        self.region = region_name

    def create_knowledge_base(self, kb_name, kb_description, embedding_model_arn=None):
        """Create a new knowledge base

        :param kb_name: Name for the knowledge base
        :param kb_description: Description for the knowledge base
        :param embedding_model_arn: ARN of the embedding model to use (default: Cohere Embed English)
        :return: Knowledge base ID if creation was successful, None otherwise
        """
        try:
            # Use Cohere Embed English if no model ARN is provided
            if not embedding_model_arn:
                embedding_model_arn = f"arn:aws:bedrock:{self.region}::foundation-model/cohere.embed-english-v3"
                logger.info(f"Using default embedding model: {embedding_model_arn}")

            # Create IAM role ARN for the knowledge base
            # Note: In a real implementation, this would use proper IAM role management
            # Here we assume a role already exists
            role_arn = f"arn:aws:iam::836255806547:role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase"

            # Create the knowledge base
            response = self.bedrock_agent_client.create_knowledge_base(
                name=kb_name,
                description=kb_description,
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": embedding_model_arn
                    }
                },
                storageConfiguration={
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": f"arn:aws:aoss:{self.region}:836255806547:collection/{kb_name.lower().replace('-', '')[:32]}",
                        "vectorIndexName": f"{kb_name.lower().replace('-', '_')}_index",
                        "fieldMapping": {
                            "vectorField": "vector",
                            "textField": "text",
                            "metadataField": "metadata"
                        }
                    }
                }
            )

            kb_id = response['knowledgeBaseId']
            logger.info(f"Created knowledge base: {kb_id}")

            # Wait for knowledge base to be ready
            logger.info("Waiting for knowledge base to be ready...")
            waiter_delay = 5  # seconds
            waiter_max_attempts = 60  # 5 minutes max

            for attempt in range(waiter_max_attempts):
                kb_response = self.bedrock_agent_client.get_knowledge_base(
                    knowledgeBaseId=kb_id
                )
                status = kb_response.get('status')

                if status == 'READY':
                    logger.info("Knowledge base is ready.")
                    break
                elif status in ['CREATING', 'UPDATING']:
                    logger.info(f"Knowledge base status: {status}, waiting...")
                    time.sleep(waiter_delay)
                else:
                    logger.error(f"Unexpected knowledge base status: {status}")
                    return None

            return kb_id
        except ClientError as e:
            logger.error(f"Error creating knowledge base: {e}")
            return None

    def create_data_source(self, kb_id, ds_name, ds_description, s3_bucket, s3_prefix):
        """Create a data source for the knowledge base

        :param kb_id: Knowledge base ID
        :param ds_name: Name for the data source
        :param ds_description: Description for the data source
        :param s3_bucket: S3 bucket name
        :param s3_prefix: S3 prefix for the data
        :return: Data source ID if creation was successful, None otherwise
        """
        try:
            response = self.bedrock_agent_client.create_data_source(
                knowledgeBaseId=kb_id,
                name=ds_name,
                description=ds_description,
                dataSourceConfiguration={
                    "type": "S3",
                    "s3Configuration": {
                        "bucketName": s3_bucket,
                        "inclusionPrefixes": [s3_prefix] if s3_prefix else []
                    }
                },
                vectorIngestionConfiguration={
                    "chunkingConfiguration": {
                        "chunkingStrategy": "HIERARCHICAL",
                        "hierarchicalChunkingConfiguration": {
                            "levelConfigurations": [
                                {
                                    "maxTokens": PARENT_CHUNK_MAX_TOKENS
                                },
                                {
                                    "maxTokens": CHILD_CHUNK_MAX_TOKENS
                                }
                            ],
                            "overlapTokens": CHUNK_OVERLAP_TOKENS
                        }
                    }
                }
            )

            ds_id = response['dataSourceId']
            logger.info(f"Created data source: {ds_id}")

            # Wait for data source to be ready
            logger.info("Waiting for data source to be ready...")
            waiter_delay = 5  # seconds
            waiter_max_attempts = 60  # 5 minutes max

            for attempt in range(waiter_max_attempts):
                ds_response = self.bedrock_agent_client.get_data_source(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id
                )
                status = ds_response.get('status')

                if status == 'READY':
                    logger.info("Data source is ready.")
                    break
                elif status in ['CREATING', 'UPDATING']:
                    logger.info(f"Data source status: {status}, waiting...")
                    time.sleep(waiter_delay)
                else:
                    logger.error(f"Unexpected data source status: {status}")
                    return None

            return ds_id
        except ClientError as e:
            logger.error(f"Error creating data source: {e}")
            return None

    def start_ingestion_job(self, kb_id, ds_id):
        """Start an ingestion job for the data source

        :param kb_id: Knowledge base ID
        :param ds_id: Data source ID
        :return: Ingestion job ID if creation was successful, None otherwise
        """
        try:
            response = self.bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id
            )

            job_id = response['ingestionJobId']
            logger.info(f"Started ingestion job: {job_id}")

            # Wait for ingestion job to complete
            logger.info("Waiting for ingestion job to complete...")
            waiter_delay = 10  # seconds
            waiter_max_attempts = 180  # 30 minutes max

            for attempt in range(waiter_max_attempts):
                job_response = self.bedrock_agent_client.get_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id,
                    ingestionJobId=job_id
                )
                status = job_response.get('status')

                if status == 'COMPLETE':
                    logger.info("Ingestion job completed successfully.")
                    break
                elif status == 'FAILED':
                    logger.error(f"Ingestion job failed: {job_response.get('failureReason', 'Unknown reason')}")
                    return None
                elif status in ['STARTING', 'IN_PROGRESS']:
                    logger.info(f"Ingestion job status: {status}, waiting...")
                    time.sleep(waiter_delay)
                else:
                    logger.error(f"Unexpected ingestion job status: {status}")
                    return None
            else:
                logger.warning("Ingestion job taking longer than expected. Continuing without waiting for completion.")

            return job_id
        except ClientError as e:
            logger.error(f"Error starting ingestion job: {e}")
            return None

    def configure_hybrid_search(self, kb_id, embedding_model_arn=None, vector_search_weight=0.7, keyword_search_weight=0.3):
        """Configure hybrid search for the knowledge base

        :param kb_id: Knowledge base ID
        :param embedding_model_arn: ARN of the embedding model
        :param vector_search_weight: Weight for vector search (0.0 to 1.0)
        :param keyword_search_weight: Weight for keyword search (0.0 to 1.0)
        :return: True if configuration was successful, False otherwise
        """
        try:
            # Use Cohere Embed English if no model ARN is provided
            if not embedding_model_arn:
                embedding_model_arn = f"arn:aws:bedrock:{self.region}::foundation-model/cohere.embed-english-v3"
                logger.info(f"Using default embedding model: {embedding_model_arn}")

            response = self.bedrock_agent_client.update_knowledge_base(
                knowledgeBaseId=kb_id,
                knowledgeBaseConfiguration={
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": embedding_model_arn,
                        "searchConfiguration": {
                            "hybridSearchConfiguration": {
                                "enabled": True,
                                "vectorSearchWeight": vector_search_weight,
                                "keywordSearchWeight": keyword_search_weight
                            }
                        }
                    }
                }
            )

            logger.info(f"Configured hybrid search for knowledge base: {kb_id}")
            return True
        except ClientError as e:
            logger.error(f"Error configuring hybrid search: {e}")
            return False

    def test_retrieval(self, kb_id, query_text, num_results=5):
        """Test retrieval from the knowledge base

        :param kb_id: Knowledge base ID
        :param query_text: Query text
        :param num_results: Number of results to retrieve
        :return: Retrieved results or None if retrieval failed
        """
        try:
            response = self.bedrock_agent_runtime_client.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={
                    'text': query_text
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': num_results
                    }
                }
            )

            results = response.get('retrievalResults', [])
            logger.info(f"Retrieved {len(results)} results for query: {query_text}")

            # Print a summary of the results
            for i, result in enumerate(results):
                doc_id = result.get('location', {}).get('s3Location', {}).get('uri', 'Unknown')
                score = result.get('score', 0)
                content_sample = result.get('content', {}).get('text', '')[:100] + '...' if result.get('content', {}).get('text') else ''
                logger.info(f"Result {i+1}: Score={score:.4f}, Document={doc_id}")
                logger.info(f"Content sample: {content_sample}")

            return results
        except ClientError as e:
            logger.error(f"Error retrieving from knowledge base: {e}")
            return None

def create_and_configure_knowledge_base(kb_name, kb_description, s3_bucket, s3_prefix, region_name='us-east-1', test_query=None):
    """End-to-end function to create and configure a knowledge base with a data source

    :param kb_name: Name for the knowledge base
    :param kb_description: Description for the knowledge base
    :param s3_bucket: S3 bucket name containing the documentation
    :param s3_prefix: S3 prefix for the documentation
    :param region_name: AWS region
    :param test_query: Optional test query to run after setup
    :return: Knowledge base ID and data source ID if successful, None otherwise
    """
    kb_setup = BedrockKnowledgeBaseSetup(region_name)

    # Create knowledge base
    kb_id = kb_setup.create_knowledge_base(kb_name, kb_description)
    if not kb_id:
        logger.error("Failed to create knowledge base")
        return None, None

    # Create data source
    ds_name = f"{kb_name}-data-source"
    ds_description = f"Documentation data source for {kb_name}"
    ds_id = kb_setup.create_data_source(kb_id, ds_name, ds_description, s3_bucket, s3_prefix)
    if not ds_id:
        logger.error("Failed to create data source")
        return kb_id, None

    # Start ingestion job
    job_id = kb_setup.start_ingestion_job(kb_id, ds_id)
    if not job_id:
        logger.error("Failed to start ingestion job")
        return kb_id, ds_id

    # Configure hybrid search
    if not kb_setup.configure_hybrid_search(kb_id):
        logger.error("Failed to configure hybrid search, but continuing with basic search")

    # Test retrieval if a test query is provided
    if test_query:
        logger.info(f"Testing retrieval with query: {test_query}")
        results = kb_setup.test_retrieval(kb_id, test_query)
        if results:
            logger.info(f"Retrieval test successful, found {len(results)} results")
        else:
            logger.warning("Retrieval test failed or returned no results")

    logger.info(f"Knowledge base setup complete. Knowledge base ID: {kb_id}, Data source ID: {ds_id}")
    return kb_id, ds_id

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Set up Amazon Bedrock Knowledge Base')
    parser.add_argument('--name', default='pic-dbkb', help='Knowledge base name')
    parser.add_argument('--description', default='Database Schema Knowledge Base', help='Knowledge base description')
    parser.add_argument('--bucket', required=True, help='S3 bucket name containing documentation')
    parser.add_argument('--prefix', default='dbkb', help='S3 prefix for documentation')
    parser.add_argument('--region', default='us-east-1', help='AWS region name')
    parser.add_argument('--test-query', help='Test query to run after setup')

    args = parser.parse_args()

    kb_id, ds_id = create_and_configure_knowledge_base(
        args.name,
        args.description,
        args.bucket,
        args.prefix,
        args.region,
        args.test_query
    )

    if kb_id:
        print(f"Knowledge base created successfully: {kb_id}")
        if ds_id:
            print(f"Data source created successfully: {ds_id}")
    else:
        print("Knowledge base creation failed")
        exit(1)
