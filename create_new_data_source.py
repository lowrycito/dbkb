#!/usr/bin/env python3
"""
Create new data source with hierarchical chunking for knowledge base KRD3MW7QFS
"""
import boto3
import json
import logging
import time
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_hierarchical_data_source(kb_id):
    """Create new data source with hierarchical chunking"""
    print(f"🚀 CREATING NEW DATA SOURCE WITH HIERARCHICAL CHUNKING")
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name="pic-database-kb-hierarchical",
            description="Database knowledge base with hierarchical chunking (512/300/50 tokens)",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": "arn:aws:s3:::pic-dbkb",
                    "inclusionPrefixes": ["dbkb/"]
                }
            },
            vectorIngestionConfiguration={
                "chunkingConfiguration": {
                    "chunkingStrategy": "HIERARCHICAL",
                    "hierarchicalChunkingConfiguration": {
                        "levelConfigurations": [
                            {
                                "maxTokens": 512  # Parent chunks (max for cohere.embed-english-v3)
                            },
                            {
                                "maxTokens": 300   # Child chunks for precise retrieval
                            }
                        ],
                        "overlapTokens": 50
                    }
                }
            }
        )
        
        new_data_source_id = response['dataSource']['dataSourceId']
        print(f"✅ Created new data source: {new_data_source_id}")
        print(f"Status: {response['dataSource']['status']}")
        
        return new_data_source_id
        
    except Exception as e:
        print(f"❌ Error creating data source: {e}")
        return None

def start_ingestion_job(kb_id, data_source_id):
    """Start ingestion job for the new data source"""
    print(f"\n🔄 STARTING INGESTION JOB FOR NEW DATA SOURCE...")
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            description="Initial ingestion with hierarchical chunking (512/300/50 tokens) and semantic markers"
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"✅ Started ingestion job: {job_id}")
        print(f"Status: {response['ingestionJob']['status']}")
        
        return job_id
        
    except Exception as e:
        print(f"❌ Error starting ingestion job: {e}")
        return None

def monitor_ingestion_job(kb_id, data_source_id, job_id, max_wait_minutes=15):
    """Monitor ingestion job progress"""
    print(f"\n⏳ MONITORING INGESTION JOB: {job_id}")
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            response = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                ingestionJobId=job_id
            )
            
            job = response['ingestionJob']
            status = job['status']
            
            print(f"Status: {status}")
            
            if status == 'COMPLETE':
                print("✅ Ingestion job completed successfully!")
                if 'statistics' in job:
                    stats = job['statistics']
                    print(f"Documents processed: {stats.get('numberOfDocumentsScanned', 'N/A')}")
                    print(f"Documents indexed: {stats.get('numberOfNewDocumentsIndexed', 'N/A')}")
                    print(f"Documents failed: {stats.get('numberOfDocumentsFailed', 'N/A')}")
                return True
            elif status == 'FAILED':
                print("❌ Ingestion job failed!")
                if 'failureReasons' in job:
                    for reason in job['failureReasons']:
                        print(f"Failure reason: {reason}")
                return False
            elif status in ['STARTING', 'IN_PROGRESS']:
                print(f"Job in progress... waiting 30 seconds")
                time.sleep(30)
            else:
                print(f"Unexpected status: {status}")
                time.sleep(30)
        
        print(f"⚠️ Job still running after {max_wait_minutes} minutes")
        return False
        
    except Exception as e:
        print(f"❌ Error monitoring ingestion job: {e}")
        return False

def delete_old_data_source(kb_id, old_data_source_id):
    """Delete the old semantic chunking data source"""
    print(f"\n🗑️ DELETING OLD DATA SOURCE: {old_data_source_id}")
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        response = bedrock_agent.delete_data_source(
            knowledgeBaseId=kb_id,
            dataSourceId=old_data_source_id
        )
        
        print("✅ Old data source deleted successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting old data source: {e}")
        return False

def test_knowledge_base_with_hierarchical_chunking(kb_id):
    """Test the knowledge base with hierarchical chunking"""
    print(f"\n🧪 TESTING KNOWLEDGE BASE WITH HIERARCHICAL CHUNKING...")
    
    try:
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        test_queries = [
            "Show me the customers table structure",
            "How do I join customers with orders?", 
            "Get all active customers from the database",
            "Create a query to find customers with recent orders"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: {query} ---")
            
            try:
                response = bedrock_runtime.retrieve_and_generate(
                    input={'text': query},
                    retrieveAndGenerateConfiguration={
                        'type': 'KNOWLEDGE_BASE',
                        'knowledgeBaseConfiguration': {
                            'knowledgeBaseId': kb_id,
                            'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
                        }
                    }
                )
                
                response_text = response['output']['text']
                print(f"Response length: {len(response_text)} characters")
                
                sql_keywords = ['select', 'from', 'where', 'join', 'create', 'table', 'insert', 'update', 'delete']
                has_sql = any(keyword in response_text.lower() for keyword in sql_keywords)
                
                lines = response_text.strip().split('\n')
                sql_lines = [line for line in lines if any(kw in line.lower() for kw in sql_keywords)]
                sql_ratio = len(sql_lines) / len(lines) if lines else 0
                
                print(f"✅ Contains SQL: {has_sql}")
                print(f"✅ SQL-focused ratio: {sql_ratio:.2f}")
                print(f"Preview: {response_text[:300]}...")
                
                if sql_ratio > 0.3:
                    print("✅ Response appears SQL-focused")
                else:
                    print("⚠️ Response may contain too much explanatory text")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing knowledge base: {e}")
        return False

def main():
    kb_id = "KRD3MW7QFS"
    old_data_source_id = "PFF80JIRZB"  # From previous test
    
    print("🚀 REPLACING DATA SOURCE WITH HIERARCHICAL CHUNKING")
    print("=" * 60)
    
    new_data_source_id = create_hierarchical_data_source(kb_id)
    if not new_data_source_id:
        print("❌ Failed to create new data source")
        return
    
    job_id = start_ingestion_job(kb_id, new_data_source_id)
    if not job_id:
        print("❌ Failed to start ingestion job")
        return
    
    if not monitor_ingestion_job(kb_id, new_data_source_id, job_id):
        print("⚠️ Ingestion job did not complete within timeout")
        print("Check job status in AWS Console before proceeding")
        return
    
    test_knowledge_base_with_hierarchical_chunking(kb_id)
    
    print(f"\n🤔 Ready to delete old data source {old_data_source_id}?")
    print("Uncomment the line below to delete the old semantic chunking data source")
    
    print("\n" + "=" * 60)
    print("🎉 KNOWLEDGE BASE UPDATE COMPLETE!")
    print(f"Knowledge Base ID: {kb_id}")
    print(f"New Data Source ID: {new_data_source_id}")
    print("Hierarchical Chunking: 512/300/50 tokens (Cohere-compatible)")
    print("SQL-focused prompts: Ready for testing")
    print("Semantic markers: Applied in documentation")

if __name__ == "__main__":
    main()
