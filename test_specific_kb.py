#!/usr/bin/env python3
"""
Test the specific knowledge base KRD3MW7QFS with hierarchical chunking improvements
"""
import boto3
import json
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_knowledge_base_details(kb_id):
    """Get detailed information about the knowledge base"""
    print(f"🔍 CHECKING KNOWLEDGE BASE: {kb_id}")
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
        kb = kb_response['knowledgeBase']
        
        print(f"  ✅ Name: {kb['name']}")
        print(f"  ✅ Status: {kb['status']}")
        print(f"  ✅ Role: {kb['roleArn']}")
        print(f"  ✅ Storage Type: {kb['storageConfiguration']['type']}")
        
        ds_response = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
        data_sources = ds_response['dataSourceSummaries']
        
        print(f"  ✅ Data Sources: {len(data_sources)}")
        for ds in data_sources:
            print(f"    - {ds['name']} ({ds['status']}) - {ds['dataSourceId']}")
            
            try:
                ds_detail = bedrock_agent.get_data_source(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds['dataSourceId']
                )
                ds_info = ds_detail['dataSource']
                
                if 's3Configuration' in ds_info['dataSourceConfiguration']:
                    s3_config = ds_info['dataSourceConfiguration']['s3Configuration']
                    print(f"      S3 Bucket: {s3_config['bucketArn']}")
                    if 'inclusionPrefixes' in s3_config:
                        print(f"      Prefixes: {s3_config['inclusionPrefixes']}")
                
                if 'vectorIngestionConfiguration' in ds_info:
                    vec_config = ds_info['vectorIngestionConfiguration']
                    if 'chunkingConfiguration' in vec_config:
                        chunk_config = vec_config['chunkingConfiguration']
                        print(f"      Chunking Strategy: {chunk_config['chunkingStrategy']}")
                        
                        if chunk_config['chunkingStrategy'] == 'HIERARCHICAL':
                            hier_config = chunk_config['hierarchicalChunkingConfiguration']
                            levels = hier_config['levelConfigurations']
                            print(f"      Parent Tokens: {levels[0]['maxTokens']}")
                            print(f"      Child Tokens: {levels[1]['maxTokens']}")
                            print(f"      Overlap Tokens: {hier_config['overlapTokens']}")
                        elif chunk_config['chunkingStrategy'] == 'SEMANTIC':
                            sem_config = chunk_config['semanticChunkingConfiguration']
                            print(f"      Max Tokens: {sem_config['maxTokens']}")
                            print(f"      Buffer Size: {sem_config['bufferSize']}")
                        
            except Exception as e:
                print(f"      Error getting data source details: {e}")
        
        return kb, data_sources
        
    except Exception as e:
        print(f"❌ Error getting knowledge base details: {e}")
        return None, []

def test_knowledge_base_query(kb_id):
    """Test querying the knowledge base"""
    print(f"\n🧪 TESTING KNOWLEDGE BASE QUERY: {kb_id}")
    
    try:
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        test_query = "Show me the customers table structure"
        
        print(f"Query: {test_query}")
        
        response = bedrock_runtime.retrieve_and_generate(
            input={
                'text': test_query
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_id,
                    'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
                }
            }
        )
        
        print("✅ Query successful!")
        print(f"Response: {response['output']['text'][:500]}...")
        
        response_text = response['output']['text'].lower()
        has_sql = any(keyword in response_text for keyword in ['select', 'from', 'where', 'join', 'create table'])
        print(f"Contains SQL keywords: {has_sql}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error testing knowledge base query: {e}")
        return None

def update_data_source_with_new_docs(kb_id, data_source_id):
    """Start ingestion job to update data source with new documentation"""
    print(f"\n🔄 UPDATING DATA SOURCE: {data_source_id}")
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        # Start ingestion job
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            description="Update with hierarchical chunking documentation"
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"✅ Started ingestion job: {job_id}")
        print(f"Status: {response['ingestionJob']['status']}")
        
        return job_id
        
    except Exception as e:
        print(f"❌ Error starting ingestion job: {e}")
        return None

def main():
    kb_id = "KRD3MW7QFS"  # User's database knowledge base
    
    print("🚀 TESTING SPECIFIC KNOWLEDGE BASE")
    print("=" * 50)
    
    kb, data_sources = get_knowledge_base_details(kb_id)
    
    if not kb:
        print("❌ Could not retrieve knowledge base details")
        return
    
    response = test_knowledge_base_query(kb_id)
    
    if data_sources:
        print(f"\n🎯 RECOMMENDATIONS:")
        
        needs_update = False
        for ds in data_sources:
            print(f"Data Source: {ds['name']}")
            if ds['status'] != 'AVAILABLE':
                print(f"  ⚠️  Status is {ds['status']} - may need refresh")
                needs_update = True
        
        if needs_update:
            print("\n🔄 Consider updating data sources with new documentation")
        else:
            print("\n✅ Knowledge base appears to be working correctly")
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    print(f"Knowledge Base ID: {kb_id}")
    print(f"Status: {kb['status'] if kb else 'Unknown'}")
    print(f"Query Test: {'✅ Passed' if response else '❌ Failed'}")
    print(f"Data Sources: {len(data_sources)} found")

if __name__ == "__main__":
    main()
