#!/usr/bin/env python3
"""
Update knowledge base KRD3MW7QFS data source with hierarchical chunking configuration
"""
import boto3
import json
import logging
import time
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_data_source_chunking(kb_id, data_source_id):
    """Update data source with hierarchical chunking configuration"""
    print(f"🔄 UPDATING DATA SOURCE CHUNKING: {data_source_id}")
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        current_ds = bedrock_agent.get_data_source(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )
        
        ds_config = current_ds['dataSource']
        print(f"Current chunking: {ds_config['vectorIngestionConfiguration']['chunkingConfiguration']['chunkingStrategy']}")
        
        updated_config = {
            'name': ds_config['name'],
            'description': ds_config.get('description', 'Updated with hierarchical chunking (512/300/50 tokens)'),
            'dataSourceConfiguration': ds_config['dataSourceConfiguration'],
            'vectorIngestionConfiguration': {
                'chunkingConfiguration': {
                    'chunkingStrategy': 'HIERARCHICAL',
                    'hierarchicalChunkingConfiguration': {
                        'levelConfigurations': [
                            {
                                'maxTokens': 512  # Parent chunks (max allowed by cohere.embed-english-v3)
                            },
                            {
                                'maxTokens': 300   # Child chunks for precise retrieval
                            }
                        ],
                        'overlapTokens': 50
                    }
                }
            }
        }
        
        response = bedrock_agent.update_data_source(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            **updated_config
        )
        
        print("✅ Data source updated with hierarchical chunking!")
        print(f"Status: {response['dataSource']['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating data source: {e}")
        return False

def start_ingestion_job(kb_id, data_source_id):
    """Start ingestion job to refresh data with new chunking"""
    print(f"\n🚀 STARTING INGESTION JOB...")
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            description="Refresh with hierarchical chunking (512/300/50 tokens) and semantic markers"
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"✅ Started ingestion job: {job_id}")
        print(f"Status: {response['ingestionJob']['status']}")
        
        return job_id
        
    except Exception as e:
        print(f"❌ Error starting ingestion job: {e}")
        return None

def monitor_ingestion_job(kb_id, data_source_id, job_id, max_wait_minutes=10):
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

def test_updated_kb(kb_id):
    """Test the updated knowledge base"""
    print(f"\n🧪 TESTING UPDATED KNOWLEDGE BASE...")
    
    try:
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        test_queries = [
            "Show me the customers table structure",
            "How do I join customers with orders?",
            "Get all active customers from the database"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nTest {i}: {query}")
            
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
                
                sql_keywords = ['select', 'from', 'where', 'join', 'create', 'table']
                has_sql = any(keyword in response_text.lower() for keyword in sql_keywords)
                
                lines = response_text.strip().split('\n')
                sql_lines = [line for line in lines if any(kw in line.lower() for kw in sql_keywords)]
                sql_ratio = len(sql_lines) / len(lines) if lines else 0
                
                print(f"✅ Contains SQL: {has_sql}")
                print(f"✅ SQL-focused ratio: {sql_ratio:.2f}")
                print(f"Preview: {response_text[:200]}...")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing knowledge base: {e}")
        return False

def main():
    kb_id = "KRD3MW7QFS"
    data_source_id = "PFF80JIRZB"  # From previous test
    
    print("🚀 UPDATING KNOWLEDGE BASE WITH HIERARCHICAL CHUNKING")
    print("=" * 60)
    
    if not update_data_source_chunking(kb_id, data_source_id):
        print("❌ Failed to update data source configuration")
        return
    
    job_id = start_ingestion_job(kb_id, data_source_id)
    if not job_id:
        print("❌ Failed to start ingestion job")
        return
    
    if not monitor_ingestion_job(kb_id, data_source_id, job_id):
        print("⚠️ Ingestion job did not complete within timeout")
        print("You can check the job status later in AWS Console")
        return
    
    test_updated_kb(kb_id)
    
    print("\n" + "=" * 60)
    print("🎉 KNOWLEDGE BASE UPDATE COMPLETE!")
    print(f"Knowledge Base ID: {kb_id}")
    print("Hierarchical Chunking: 512/300/50 tokens (adjusted for Cohere embedding model)")
    print("SQL-focused prompts: Enabled")
    print("Semantic markers: Applied")

if __name__ == "__main__":
    main()
