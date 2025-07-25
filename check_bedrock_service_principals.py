#!/usr/bin/env python3
"""
Check what service principals Bedrock Knowledge Base actually needs
"""
import boto3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_different_trust_policies():
    """Test different service principal combinations"""
    
    trust_policy_v1 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    trust_policy_v2 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": "836255806547"
                    }
                }
            }
        ]
    }
    
    print("Trust Policy V1 (current):")
    print(json.dumps(trust_policy_v1, indent=2))
    print("\nTrust Policy V2 (with condition):")
    print(json.dumps(trust_policy_v2, indent=2))
    
    return trust_policy_v2

if __name__ == "__main__":
    policy = test_different_trust_policies()
    
    with open('bedrock-trust-policy-v2.json', 'w') as f:
        json.dump(policy, f, indent=2)
    
    print("\n✅ Created bedrock-trust-policy-v2.json with account condition")
