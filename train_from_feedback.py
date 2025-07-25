#!/usr/bin/env python3
"""
CLI tool to process feedback and update knowledge bases
"""
import argparse
import sys
import os
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_chat_db_connection
from src.training.feedback_processor import FeedbackProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Process feedback and update knowledge bases')
    parser.add_argument('--kb-id', required=True, help='Knowledge base ID to process')
    parser.add_argument('--company-id', type=int, required=True, help='Company ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without making changes')
    
    args = parser.parse_args()
    
    try:
        connection = get_chat_db_connection()
        if not connection:
            logger.error("Could not connect to database")
            return 1
        
        processor = FeedbackProcessor()
        
        if args.dry_run:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT COUNT(*) as count FROM query_feedback 
                   WHERE KnowledgeBaseId = %s AND CompanyId = %s 
                   AND ProcessingStatus = 'pending' AND FeedbackType = 'correction'""",
                (args.kb_id, args.company_id)
            )
            result = cursor.fetchone()
            cursor.close()
            
            print(f"Would process {result['count']} pending feedback items for KB {args.kb_id}")
        else:
            result = processor.process_pending_feedback(args.kb_id, args.company_id, connection)
            print(f"Processed {result.get('processed', 0)} feedback items")
            print(f"Status: {result.get('status')}")
        
        connection.close()
        return 0
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
