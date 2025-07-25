#!/usr/bin/env python3
"""
Create OpenSearch Serverless security policies required for Bedrock Knowledge Base
"""
import boto3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_encryption_policy(client, collection_name):
    """Create encryption security policy"""
    policy_name = f"{collection_name}-encryption-policy"
    
    policy_document = {
        "Rules": [
            {
                "Resource": [f"collection/{collection_name}"],
                "ResourceType": "collection"
            }
        ],
        "AWSOwnedKey": True
    }
    
    try:
        response = client.create_security_policy(
            name=policy_name,
            type='encryption',
            policy=json.dumps(policy_document),
            description=f'Encryption policy for {collection_name} collection'
        )
        logger.info(f"Created encryption policy: {policy_name}")
        return response
    except client.exceptions.ConflictException:
        logger.info(f"Encryption policy {policy_name} already exists")
        return None
    except Exception as e:
        logger.error(f"Error creating encryption policy: {e}")
        return None

def create_network_policy(client, collection_name):
    """Create network security policy"""
    policy_name = f"{collection_name}-network-policy"
    
    policy_document = [
        {
            "Rules": [
                {
                    "Resource": [f"collection/{collection_name}"],
                    "ResourceType": "collection"
                },
                {
                    "Resource": [f"collection/{collection_name}"],
                    "ResourceType": "dashboard"
                }
            ],
            "AllowFromPublic": True
        }
    ]
    
    try:
        response = client.create_security_policy(
            name=policy_name,
            type='network',
            policy=json.dumps(policy_document),
            description=f'Network policy for {collection_name} collection'
        )
        logger.info(f"Created network policy: {policy_name}")
        return response
    except client.exceptions.ConflictException:
        logger.info(f"Network policy {policy_name} already exists")
        return None
    except Exception as e:
        logger.error(f"Error creating network policy: {e}")
        return None

def create_data_access_policy(client, collection_name, account_id):
    """Create data access policy"""
    policy_name = f"{collection_name}-data-policy"
    
    policy_document = [
        {
            "Rules": [
                {
                    "Resource": [f"collection/{collection_name}"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:DeleteCollectionItems", 
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems"
                    ],
                    "ResourceType": "collection"
                },
                {
                    "Resource": [f"index/{collection_name}/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:DeleteIndex",
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument"
                    ],
                    "ResourceType": "index"
                }
            ],
            "Principal": [
                f"arn:aws:iam::{account_id}:role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase"
            ],
            "Description": f"Data access policy for {collection_name}"
        }
    ]
    
    try:
        response = client.create_access_policy(
            name=policy_name,
            type='data',
            policy=json.dumps(policy_document),
            description=f'Data access policy for {collection_name} collection'
        )
        logger.info(f"Created data access policy: {policy_name}")
        return response
    except client.exceptions.ConflictException:
        logger.info(f"Data access policy {policy_name} already exists")
        return None
    except Exception as e:
        logger.error(f"Error creating data access policy: {e}")
        return None

def main():
    collection_name = "picdbkb"  # Same as kb_name.lower().replace('-', '')[:32]
    account_id = "836255806547"
    
    try:
        client = boto3.client('opensearchserverless', region_name='us-east-1')
        
        logger.info(f"Creating security policies for collection: {collection_name}")
        
        create_encryption_policy(client, collection_name)
        
        create_network_policy(client, collection_name)
        
        create_data_access_policy(client, collection_name, account_id)
        
        logger.info("Security policies creation completed")
        
    except Exception as e:
        logger.error(f"Error creating security policies: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ OpenSearch Serverless security policies created successfully")
    else:
        print("❌ Failed to create security policies")
        exit(1)
