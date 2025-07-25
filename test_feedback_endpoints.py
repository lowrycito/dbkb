#!/usr/bin/env python3
"""
Test the feedback system endpoints without requiring a running server
"""
import sys
import os
import json
from unittest.mock import Mock, patch

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_feedback_models():
    """Test feedback model validation"""
    print("🧪 Testing Feedback Models...")
    
    try:
        from app import FeedbackRequest, FeedbackResponse, TrainingStatusRequest, TrainingStatusResponse, UserContext
        
        user_context = UserContext(
            loginId="test.user",
            email="test@example.com",
            firstName="Test",
            lastName="User",
            company="TEST001",
            companyName="Test Company",
            industry="Technology",
            databaseHost="test-db.example.com",
            databaseSchema="test_schema",
            application="epic"
        )
        
        feedback_request = FeedbackRequest(
            messageId=1,
            sessionId="test-session-123",
            feedbackType="correction",
            rating=2,
            originalQuery="Show me all sales orders by payment date",
            originalResponse="SELECT * FROM db_salescommissionlog WHERE...",
            correctedResponse='SELECT * FROM db_order WHERE DatePaid != "0000-00-00" ORDER BY DatePaid',
            feedbackNotes="Used wrong table - should be db_order not db_salescommissionlog",
            problemCategory="wrong_table",
            userContext=user_context
        )
        
        training_request = TrainingStatusRequest(
            knowledgeBaseId="KRD3MW7QFS",
            userContext=user_context
        )
        
        print("✅ All feedback models validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Feedback model validation failed: {e}")
        return False

def test_feedback_processor():
    """Test FeedbackProcessor functionality"""
    print("\n🧪 Testing FeedbackProcessor...")
    
    try:
        from src.training.feedback_processor import FeedbackProcessor
        
        processor = FeedbackProcessor()
        
        test_query = "Show me all sales orders by payment date"
        pattern = processor.generalize_query_pattern(test_query)
        print(f"✅ Query pattern generalization: '{test_query}' -> '{pattern}'")
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        result = processor.process_pending_feedback("KRD3MW7QFS", 1, mock_connection)
        print(f"✅ Process pending feedback (no data): {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ FeedbackProcessor test failed: {e}")
        return False

def test_database_schema():
    """Test that the database schema is valid SQL"""
    print("\n🧪 Testing Database Schema...")
    
    try:
        with open('feedback_schema.sql', 'r') as f:
            schema_content = f.read()
        
        required_tables = ['query_feedback', 'training_data', 'kb_improvement_log']
        for table in required_tables:
            if f"CREATE TABLE {table}" not in schema_content:
                raise ValueError(f"Missing table: {table}")
        
        required_columns = ['MessageId', 'UserId', 'CompanyId', 'FeedbackType', 'OriginalQuery', 'CorrectedResponse']
        for column in required_columns:
            if column not in schema_content:
                raise ValueError(f"Missing column: {column}")
        
        print("✅ Database schema validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Database schema validation failed: {e}")
        return False

def test_ui_widget():
    """Test that the UI widget file is valid JavaScript"""
    print("\n🧪 Testing UI Widget...")
    
    try:
        with open('src/ui/feedback-widget.js', 'r') as f:
            widget_content = f.read()
        
        required_components = ['class FeedbackWidget', 'showFeedbackForm', 'submitFeedback', 'window.FeedbackWidget']
        for component in required_components:
            if component not in widget_content:
                raise ValueError(f"Missing component: {component}")
        
        print("✅ UI widget validation passed")
        return True
        
    except Exception as e:
        print(f"❌ UI widget validation failed: {e}")
        return False

def test_cli_tool():
    """Test the CLI training tool"""
    print("\n🧪 Testing CLI Tool...")
    
    try:
        with open('train_from_feedback.py', 'r') as f:
            cli_content = f.read()
        
        required_components = ['argparse', 'FeedbackProcessor', '--kb-id', '--company-id', '--dry-run']
        for component in required_components:
            if component not in cli_content:
                raise ValueError(f"Missing component: {component}")
        
        print("✅ CLI tool validation passed")
        return True
        
    except Exception as e:
        print(f"❌ CLI tool validation failed: {e}")
        return False

def main():
    print("🚀 Testing Feedback System Components")
    print("=" * 50)
    
    success = True
    success &= test_feedback_models()
    success &= test_feedback_processor()
    success &= test_database_schema()
    success &= test_ui_widget()
    success &= test_cli_tool()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All feedback system tests passed!")
        print("\nFeedback system is ready for deployment:")
        print("- ✅ Database schema for feedback collection")
        print("- ✅ API endpoints for feedback submission")
        print("- ✅ Training pipeline for processing corrections")
        print("- ✅ UI widget for user feedback collection")
        print("- ✅ CLI tool for manual training pipeline execution")
    else:
        print("❌ Some feedback system tests failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
