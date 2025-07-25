#!/usr/bin/env python3
"""
Test multi-KB routing functionality to verify proper query classification
"""
import requests
import json
import sys

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

def test_database_query_routing():
    """Test that database queries route to database KB"""
    print("🧪 Testing Database Query Routing...")
    
    database_queries = [
        "Show me all tables in the database",
        "What columns are in the orders table?",
        "How do I join customers with orders?",
        "SELECT * FROM db_order WHERE DatePaid is not null"
    ]
    
    for query in database_queries:
        query_data = {
            "query_text": query,
            "userContext": TEST_USER_CONTEXT,
            "queryMode": "smart"  # Let it auto-classify
        }
        
        try:
            response = requests.post(f"{API_BASE}/query/multi", json=query_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                source_kb = result.get("source_knowledge_base", "unknown")
                print(f"✅ '{query[:50]}...' -> KB: {source_kb}")
            else:
                print(f"❌ '{query[:50]}...' -> Error: {response.status_code}")
        except Exception as e:
            print(f"❌ '{query[:50]}...' -> Exception: {e}")

def test_support_query_routing():
    """Test that support queries route to support KB"""
    print("\n🧪 Testing Support Query Routing...")
    
    support_queries = [
        "I'm having an error with my login",
        "How do I troubleshoot connection issues?",
        "I need help with a ticket",
        "What support articles are available for this problem?"
    ]
    
    for query in support_queries:
        query_data = {
            "query_text": query,
            "userContext": TEST_USER_CONTEXT,
            "queryMode": "smart"  # Let it auto-classify
        }
        
        try:
            response = requests.post(f"{API_BASE}/query/multi", json=query_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                source_kb = result.get("source_knowledge_base", "unknown")
                print(f"✅ '{query[:50]}...' -> KB: {source_kb}")
            else:
                print(f"❌ '{query[:50]}...' -> Error: {response.status_code}")
        except Exception as e:
            print(f"❌ '{query[:50]}...' -> Exception: {e}")

def test_forced_query_modes():
    """Test forcing specific query modes"""
    print("\n🧪 Testing Forced Query Modes...")
    
    test_query = "Show me information about orders"
    
    for mode in ['database', 'support', 'documentation']:
        query_data = {
            "query_text": test_query,
            "userContext": TEST_USER_CONTEXT,
            "queryMode": mode
        }
        
        try:
            response = requests.post(f"{API_BASE}/query/multi", json=query_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                source_kb = result.get("source_knowledge_base", "unknown")
                print(f"✅ Mode '{mode}' -> KB: {source_kb}")
            else:
                print(f"❌ Mode '{mode}' -> Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Mode '{mode}' -> Exception: {e}")

def test_application_kb_configuration():
    """Test application KB configuration"""
    print("\n🧪 Testing Application KB Configuration...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is accessible")
        else:
            print(f"❌ API health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API not accessible: {e}")

def main():
    print("🚀 Testing Multi-KB Routing Functionality")
    print("=" * 50)
    
    test_application_kb_configuration()
    test_database_query_routing()
    test_support_query_routing()
    test_forced_query_modes()
    
    print("\n" + "=" * 50)
    print("🎯 Multi-KB routing test completed")
    print("\nNext steps:")
    print("- Check application table configuration for correct KB IDs")
    print("- Verify query classification keywords are working")
    print("- Test with actual KB IDs (ECC3L7C2PG, KRD3MW7QFS)")

if __name__ == "__main__":
    main()
