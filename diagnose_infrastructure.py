#!/usr/bin/env python3
"""
Diagnose current AWS infrastructure status for knowledge base setup
"""
import boto3
import json
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_iam_roles():
    """Check IAM roles for Bedrock"""
    print("🔍 CHECKING IAM ROLES...")
    iam = boto3.client('iam')
    
    try:
        roles = iam.list_roles()['Roles']
        bedrock_roles = [r for r in roles if 'Bedrock' in r['RoleName']]
        
        print(f"Found {len(bedrock_roles)} Bedrock-related roles:")
        for role in bedrock_roles:
            print(f"  ✅ {role['RoleName']} - {role['Arn']}")
            
            trust_policy = role['AssumeRolePolicyDocument']
            services = []
            for stmt in trust_policy.get('Statement', []):
                principal = stmt.get('Principal', {})
                if isinstance(principal, dict) and 'Service' in principal:
                    service = principal['Service']
                    if isinstance(service, list):
                        services.extend(service)
                    else:
                        services.append(service)
            
            print(f"    Trust services: {', '.join(services)}")
            
            try:
                policies = iam.list_attached_role_policies(RoleName=role['RoleName'])
                policy_names = [p['PolicyName'] for p in policies['AttachedPolicies']]
                print(f"    Attached policies: {', '.join(policy_names)}")
            except Exception as e:
                print(f"    Error checking policies: {e}")
        
        return bedrock_roles
    except Exception as e:
        print(f"❌ Error checking IAM roles: {e}")
        return []

def check_opensearch_collections():
    """Check OpenSearch Serverless collections"""
    print("\n🔍 CHECKING OPENSEARCH SERVERLESS COLLECTIONS...")
    
    try:
        aoss = boto3.client('opensearchserverless', region_name='us-east-1')
        
        collections = aoss.list_collections()
        
        if collections['collectionSummaries']:
            print(f"Found {len(collections['collectionSummaries'])} collections:")
            for collection in collections['collectionSummaries']:
                print(f"  ✅ {collection['name']} - {collection['status']} - {collection['arn']}")
        else:
            print("  ❌ No collections found")
            
        return collections['collectionSummaries']
    except Exception as e:
        print(f"❌ Error checking OpenSearch collections: {e}")
        return []

def check_security_policies():
    """Check OpenSearch Serverless security policies"""
    print("\n🔍 CHECKING OPENSEARCH SECURITY POLICIES...")
    
    try:
        aoss = boto3.client('opensearchserverless', region_name='us-east-1')
        
        enc_policies = aoss.list_security_policies(type='encryption')
        print(f"Encryption policies: {len(enc_policies['securityPolicySummaries'])}")
        for policy in enc_policies['securityPolicySummaries']:
            print(f"  ✅ {policy['name']} - {policy['type']}")
        
        net_policies = aoss.list_security_policies(type='network')
        print(f"Network policies: {len(net_policies['securityPolicySummaries'])}")
        for policy in net_policies['securityPolicySummaries']:
            print(f"  ✅ {policy['name']} - {policy['type']}")
        
        data_policies = aoss.list_access_policies(type='data')
        print(f"Data access policies: {len(data_policies['accessPolicySummaries'])}")
        for policy in data_policies['accessPolicySummaries']:
            print(f"  ✅ {policy['name']} - {policy['type']}")
            
        return True
    except Exception as e:
        print(f"❌ Error checking security policies: {e}")
        return False

def check_knowledge_bases():
    """Check existing Bedrock Knowledge Bases"""
    print("\n🔍 CHECKING BEDROCK KNOWLEDGE BASES...")
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        kbs = bedrock_agent.list_knowledge_bases()
        
        if kbs['knowledgeBaseSummaries']:
            print(f"Found {len(kbs['knowledgeBaseSummaries'])} knowledge bases:")
            for kb in kbs['knowledgeBaseSummaries']:
                print(f"  ✅ {kb['name']} - {kb['status']} - {kb['knowledgeBaseId']}")
                
                try:
                    kb_detail = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb['knowledgeBaseId'])
                    kb_info = kb_detail['knowledgeBase']
                    print(f"    Role: {kb_info.get('roleArn', 'N/A')}")
                    print(f"    Storage: {kb_info.get('storageConfiguration', {}).get('type', 'N/A')}")
                except Exception as e:
                    print(f"    Error getting details: {e}")
        else:
            print("  ❌ No knowledge bases found")
            
        return kbs['knowledgeBaseSummaries']
    except Exception as e:
        print(f"❌ Error checking knowledge bases: {e}")
        return []

def check_s3_bucket():
    """Check S3 bucket status"""
    print("\n🔍 CHECKING S3 BUCKET...")
    
    try:
        s3 = boto3.client('s3')
        
        bucket_name = 'pic-dbkb'
        
        try:
            response = s3.head_bucket(Bucket=bucket_name)
            print(f"  ✅ Bucket {bucket_name} exists and accessible")
            
            objects = s3.list_objects_v2(Bucket=bucket_name, Prefix='dbkb/')
            if 'Contents' in objects:
                print(f"  ✅ Found {len(objects['Contents'])} objects with 'dbkb/' prefix")
                for obj in objects['Contents'][:5]:
                    print(f"    - {obj['Key']} ({obj['Size']} bytes)")
                if len(objects['Contents']) > 5:
                    print(f"    ... and {len(objects['Contents']) - 5} more")
            else:
                print("  ❌ No objects found with 'dbkb/' prefix")
                
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"  ❌ Bucket {bucket_name} not found")
            else:
                print(f"  ❌ Error accessing bucket: {e}")
                
        return True
    except Exception as e:
        print(f"❌ Error checking S3: {e}")
        return False

def main():
    print("🚀 DIAGNOSING AWS INFRASTRUCTURE FOR KNOWLEDGE BASE SETUP")
    print("=" * 60)
    
    iam_roles = check_iam_roles()
    collections = check_opensearch_collections()
    policies_ok = check_security_policies()
    knowledge_bases = check_knowledge_bases()
    s3_ok = check_s3_bucket()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    
    print(f"✅ IAM Roles: {len(iam_roles)} found")
    print(f"✅ OpenSearch Collections: {len(collections)} found")
    print(f"✅ Security Policies: {'OK' if policies_ok else 'MISSING'}")
    print(f"✅ Knowledge Bases: {len(knowledge_bases)} found")
    print(f"✅ S3 Bucket: {'OK' if s3_ok else 'MISSING'}")
    
    print("\n🎯 NEXT STEPS:")
    if not knowledge_bases:
        if collections and policies_ok and iam_roles:
            print("  1. All infrastructure exists - try creating knowledge base again")
            print("  2. If still failing, try using a different IAM role from the list above")
        else:
            print("  1. Missing infrastructure components need to be created")
    else:
        print("  1. Knowledge bases already exist - check if they can be reused")
        print("  2. Consider updating existing KB instead of creating new one")

if __name__ == "__main__":
    main()
