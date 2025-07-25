#!/usr/bin/env python3
"""
Test imports for the feedback system
"""
import sys
import os

def test_feedback_processor_import():
    """Test FeedbackProcessor import"""
    try:
        from src.training.feedback_processor import FeedbackProcessor
        print('✅ FeedbackProcessor import successful')
        
        processor = FeedbackProcessor()
        print('✅ FeedbackProcessor instantiation successful')
        return True
    except Exception as e:
        print(f'❌ FeedbackProcessor import failed: {e}')
        return False

def test_app_imports():
    """Test app imports"""
    try:
        from app import FeedbackRequest, FeedbackResponse, TrainingStatusRequest, TrainingStatusResponse
        print('✅ Feedback models import successful')
    except Exception as e:
        print(f'❌ Feedback models import failed: {e}')
        return False

    try:
        from app import submit_feedback, get_training_status, process_training_pipeline
        print('✅ Feedback endpoints import successful')
        return True
    except Exception as e:
        print(f'❌ Feedback endpoints import failed: {e}')
        return False

def main():
    print("🧪 Testing Feedback System Imports")
    print("=" * 40)
    
    success = True
    success &= test_feedback_processor_import()
    success &= test_app_imports()
    
    if success:
        print("\n✅ All imports successful!")
    else:
        print("\n❌ Some imports failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
