#!/usr/bin/env python3
"""
Test script to identify response truncation issues in the API pipeline
"""
import requests
import json
import sys
import time

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

def test_long_response_query():
    """Test queries that should generate long responses to check for truncation"""
    print("🧪 Testing Long Response Queries for Truncation...")
    
    long_queries = [
        "Show me the complete database schema with all tables, columns, relationships, and constraints",
        "Generate a comprehensive SQL query that joins multiple tables with detailed explanations",
        "List all database tables with their complete column definitions, data types, and relationships",
        "Create a complex SQL query with multiple JOINs, WHERE clauses, and subqueries for reporting"
    ]
    
    for query in long_queries:
        print(f"\n📝 Testing: {query[:60]}...")
        
        query_data = {
            "query_text": query,
            "userContext": TEST_USER_CONTEXT,
            "include_thinking": True,
            "include_contexts": True
        }
        
        try:
            response = requests.post(f"{API_BASE}/query", json=query_data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "")
                thinking = result.get("thinking", "")
                contexts = result.get("contexts", [])
                
                print(f"✅ Response Length: {len(answer)} characters")
                print(f"✅ Thinking Length: {len(thinking)} characters")
                print(f"✅ Contexts Count: {len(contexts)}")
                
                if answer.endswith("..."):
                    print(f"⚠️  TRUNCATION DETECTED: Answer ends with '...'")
                
                if len(answer) < 100:
                    print(f"⚠️  SUSPICIOUSLY SHORT: Answer only {len(answer)} chars")
                
                print(f"📄 Answer Preview: {answer[:200]}...")
                
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")

def test_multi_kb_response_truncation():
    """Test multi-KB queries for secondary result truncation"""
    print("\n🧪 Testing Multi-KB Response Truncation...")
    
    query_data = {
        "query_text": "I need help with database queries and also want to check support history",
        "userContext": TEST_USER_CONTEXT,
        "queryMode": "smart",
        "include_thinking": True,
        "include_contexts": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/query/multi", json=query_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            
            print(f"✅ Multi-KB Response Length: {len(answer)} characters")
            
            if "**Related Information:**" in answer:
                print("✅ Found secondary information section")
                if "..." in answer and "From" in answer:
                    print("⚠️  SECONDARY TRUNCATION DETECTED: Secondary results appear truncated")
            
            print(f"📄 Multi-KB Answer Preview: {answer[:300]}...")
            
        else:
            print(f"❌ Multi-KB Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Multi-KB Exception: {e}")

def main():
    print("🚀 Response Truncation Detection Test")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is accessible")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        print("Please start the API server with: python app.py")
        return
    
    test_long_response_query()
    test_multi_kb_response_truncation()
    
    print("\n" + "=" * 50)
    print("🎯 Truncation detection test completed")

if __name__ == "__main__":
    main()
