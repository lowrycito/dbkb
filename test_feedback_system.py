#!/usr/bin/env python3
"""
Test the feedback collection and training system
"""
import requests
import json
import sys
import os

API_BASE = "http://localhost:8000"
TEST_USER_CONTEXT = {
    "loginId": "test.user",
    "email": "test@example.com", 
    "firstName": "Test",
    "lastName": "User",
    "company": "TEST001",
    "companyName": "Test Company",
    "industry": "Technology",
    "databaseHost": "test-db.example.com",
    "databaseSchema": "test_schema",
    "application": "epic"
}

def test_feedback_submission():
    """Test submitting feedback for an incorrect response"""
    print("🧪 Testing feedback submission...")
    
    session_response = requests.post(f"{API_BASE}/chat/session", json=TEST_USER_CONTEXT)
    if session_response.status_code != 200:
        print(f"❌ Failed to create session: {session_response.text}")
        return False
    
    session_data = session_response.json()
    session_id = session_data["sessionId"]
    print(f"✅ Created session: {session_id}")
    
    query_data = {
        "query_text": "Show me all sales orders by payment date",
        "userContext": TEST_USER_CONTEXT,
        "sessionId": session_id
    }
    
    query_response = requests.post(f"{API_BASE}/query", json=query_data)
    if query_response.status_code != 200:
        print(f"❌ Failed to submit query: {query_response.text}")
        return False
    
    query_result = query_response.json()
    original_response = query_result["answer"]
    print(f"✅ Got query response: {original_response[:100]}...")
    
    message_data = {
        "sessionId": session_id,
        "messageType": "assistant",
        "content": original_response,
        "metadata": {"queryType": "general", "endpointUsed": "/query"},
        "userContext": TEST_USER_CONTEXT
    }
    
    message_response = requests.post(f"{API_BASE}/chat/message", json=message_data)
    if message_response.status_code != 200:
        print(f"❌ Failed to save message: {message_response.text}")
        return False
    
    print("✅ Saved message to database")
    
    feedback_data = {
        "messageId": 1,
        "sessionId": session_id,
        "feedbackType": "correction",
        "rating": 2,
        "originalQuery": "Show me all sales orders by payment date",
        "originalResponse": original_response,
        "correctedResponse": 'SELECT * FROM db_order WHERE DatePaid != "0000-00-00" ORDER BY DatePaid',
        "feedbackNotes": "Used wrong table - should be db_order not db_salescommissionlog",
        "problemCategory": "wrong_table",
        "userContext": TEST_USER_CONTEXT
    }
    
    feedback_response = requests.post(f"{API_BASE}/feedback", json=feedback_data)
    if feedback_response.status_code != 200:
        print(f"❌ Failed to submit feedback: {feedback_response.text}")
        return False
    
    feedback_result = feedback_response.json()
    print(f"✅ Submitted feedback: {feedback_result}")
    
    return True

def test_training_status():
    """Test getting training status"""
    print("\n🧪 Testing training status...")
    
    status_data = {
        "knowledgeBaseId": "KRD3MW7QFS",
        "userContext": TEST_USER_CONTEXT
    }
    
    status_response = requests.get(f"{API_BASE}/feedback/training-status", params=status_data)
    if status_response.status_code != 200:
        print(f"❌ Failed to get training status: {status_response.text}")
        return False
    
    status_result = status_response.json()
    print(f"✅ Training status: {status_result}")
    
    return True

def test_training_pipeline():
    """Test triggering the training pipeline"""
    print("\n🧪 Testing training pipeline...")
    
    pipeline_data = {
        "knowledgeBaseId": "KRD3MW7QFS",
        "userContext": TEST_USER_CONTEXT
    }
    
    pipeline_response = requests.post(f"{API_BASE}/feedback/process-training", json=pipeline_data)
    if pipeline_response.status_code != 200:
        print(f"❌ Failed to trigger training pipeline: {pipeline_response.text}")
        return False
    
    pipeline_result = pipeline_response.json()
    print(f"✅ Training pipeline result: {pipeline_result}")
    
    return True

def main():
    print("🚀 Testing Feedback Collection System")
    print("=" * 50)
    
    if not test_feedback_submission():
        print("❌ Feedback submission test failed")
        return 1
    
    if not test_training_status():
        print("❌ Training status test failed")
        return 1
    
    if not test_training_pipeline():
        print("❌ Training pipeline test failed")
        return 1
    
    print("\n🎉 All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
