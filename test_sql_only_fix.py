#!/usr/bin/env python3
"""
Test the SQL-only response fix for knowledge base KRD3MW7QFS using the API
"""
import requests
import json
import logging
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from advanced_retrieval.retrieval_techniques import AdvancedRetrieval

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sales_order_query():
    """Test the user's specific query about sales orders by payment date"""
    print("🧪 TESTING SQL-ONLY FIX: Sales Order Query")
    print("=" * 60)
    
    kb_id = "KRD3MW7QFS"
    user_query = "can you help me write a query to pull all sales orders by the date they were paid?"
    
    try:
        retrieval_client = AdvancedRetrieval(kb_id=kb_id)
        
        print(f"Query: {user_query}")
        print("\nSending to knowledge base via retrieval client...")
        
        result = retrieval_client.advanced_rag_query(
            user_query, 
            use_extended_thinking=False
        )
        
        response_text = result['answer']
        
        print(f"\n📝 RESPONSE ({len(response_text)} characters):")
        print("-" * 40)
        print(response_text)
        print("-" * 40)
        
        lines = response_text.strip().split('\n')
        
        explanatory_patterns = [
            'to pull', 'you can', 'this query', 'here is', 'based on',
            'the following', 'example', 'modify', 'alternatively'
        ]
        
        has_explanatory_text = any(
            any(pattern in line.lower() for pattern in explanatory_patterns)
            for line in lines
        )
        
        sql_keywords = ['select', 'from', 'where', 'join', 'order by']
        has_sql = any(keyword in response_text.lower() for keyword in sql_keywords)
        
        has_db_order = 'db_order' in response_text.lower()
        has_datepaid = 'datepaid' in response_text.lower()
        
        has_table_docs = any([
            '[TABLE:' in response_text,
            '# Table:' in response_text,
            '## Columns' in response_text,
            '| Column Name |' in response_text
        ])
        
        print(f"\n📊 SQL-ONLY COMPLIANCE CHECK:")
        print(f"✅ Contains SQL keywords: {has_sql}")
        print(f"✅ Mentions db_order table: {has_db_order}")
        print(f"✅ Mentions DatePaid column: {has_datepaid}")
        print(f"❌ Contains explanatory text: {has_explanatory_text}")
        print(f"❌ Contains table documentation: {has_table_docs}")
        
        is_sql_only = has_sql and not has_explanatory_text and not has_table_docs
        is_correct_table = has_db_order
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"✅ SQL-only response: {is_sql_only}")
        print(f"✅ Correct table identified: {is_correct_table}")
        
        if is_sql_only and is_correct_table:
            print("🎉 SUCCESS: Knowledge base returns SQL-only response with correct table!")
        else:
            print("❌ FAILED: Knowledge base still has issues")
            
        return is_sql_only and is_correct_table
        
    except Exception as e:
        print(f"❌ Error testing query: {e}")
        return False

def test_multiple_sql_queries():
    """Test multiple queries to ensure robustness"""
    print("\n🧪 TESTING MULTIPLE SQL QUERIES")
    print("=" * 60)
    
    kb_id = "KRD3MW7QFS"
    
    test_queries = [
        "Show me the customers table structure",
        "How do I join customers with orders?",
        "Get all paid orders from last month",
        "Find customers who have placed orders in 2025",
        "Show me all products with low inventory"
    ]
    
    results = []
    
    try:
        retrieval_client = AdvancedRetrieval(kb_id=kb_id)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: {query} ---")
            
            try:
                result = retrieval_client.advanced_rag_query(
                    query, 
                    use_extended_thinking=False
                )
                
                response_text = result['answer']
                
                sql_keywords = ['select', 'from', 'where', 'join']
                has_sql = any(keyword in response_text.lower() for keyword in sql_keywords)
                
                explanatory_patterns = ['you can', 'this query', 'here is', 'based on']
                has_explanatory = any(pattern in response_text.lower() for pattern in explanatory_patterns)
                
                is_sql_only = has_sql and not has_explanatory
                
                print(f"Response length: {len(response_text)} chars")
                print(f"SQL-only: {is_sql_only}")
                print(f"Preview: {response_text[:150]}...")
                
                results.append(is_sql_only)
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
                results.append(False)
        
        success_rate = sum(results) / len(results)
        print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.2f} ({sum(results)}/{len(results)})")
        
        return success_rate >= 0.8  # 80% success rate threshold
        
    except Exception as e:
        print(f"❌ Error testing multiple queries: {e}")
        return False

def main():
    print("🚀 TESTING SQL-ONLY RESPONSE FIX")
    print("=" * 60)
    
    user_query_success = test_sales_order_query()
    
    multiple_queries_success = test_multiple_sql_queries()
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    print(f"✅ User's sales order query: {user_query_success}")
    print(f"✅ Multiple queries robustness: {multiple_queries_success}")
    
    if user_query_success and multiple_queries_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("The SQL-only response fix is working correctly.")
    else:
        print("\n❌ TESTS FAILED!")
        print("The fix needs additional work.")
        
    return user_query_success and multiple_queries_success

if __name__ == "__main__":
    main()
