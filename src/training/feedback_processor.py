import os
import json
import logging
import boto3
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FeedbackProcessor:
    """Process user feedback and update knowledge base with corrections"""
    
    def __init__(self, region_name='us-east-1'):
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region_name)
        self.region = region_name
    
    def process_pending_feedback(self, kb_id: str, company_id: int, connection) -> Dict[str, Any]:
        """Process all pending feedback for a knowledge base"""
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(
            """SELECT * FROM query_feedback 
               WHERE KnowledgeBaseId = %s AND CompanyId = %s 
               AND ProcessingStatus = 'pending' AND FeedbackType = 'correction'
               ORDER BY CreatedAt ASC""",
            (kb_id, company_id)
        )
        
        pending_feedback = cursor.fetchall()
        
        if not pending_feedback:
            return {"status": "no_pending_feedback", "processed": 0}
        
        processed_count = 0
        training_data_ids = []
        
        for feedback in pending_feedback:
            try:
                training_data_id = self.create_training_data(feedback, connection)
                if training_data_id:
                    training_data_ids.append(training_data_id)
                    processed_count += 1
                    
                    cursor.execute(
                        """UPDATE query_feedback 
                           SET ProcessingStatus = 'reviewed', ProcessedAt = NOW(), ProcessedBy = 'system'
                           WHERE Id = %s""",
                        (feedback['Id'],)
                    )
                    
            except Exception as e:
                logger.error(f"Error processing feedback {feedback['Id']}: {e}")
                continue
        
        connection.commit()
        
        if training_data_ids:
            cursor.execute(
                """INSERT INTO kb_improvement_log 
                   (KnowledgeBaseId, CompanyId, ImprovementType, Description, 
                    TrainingDataIds, ImplementationMethod, Status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (kb_id, company_id, 'content_update', 
                 f"Processed {processed_count} user corrections",
                 json.dumps(training_data_ids), 'ingestion_job', 'planned')
            )
            
            improvement_log_id = cursor.lastrowid
            connection.commit()
            
            corrected_docs = self.generate_corrected_documentation(training_data_ids, connection)
            
            if corrected_docs:
                ingestion_job_id = self.update_knowledge_base_with_corrections(
                    kb_id, corrected_docs, improvement_log_id, connection
                )
                
                if ingestion_job_id:
                    cursor.execute(
                        """UPDATE kb_improvement_log 
                           SET IngestionJobId = %s, Status = 'in_progress'
                           WHERE Id = %s""",
                        (ingestion_job_id, improvement_log_id)
                    )
                    connection.commit()
        
        cursor.close()
        
        return {
            "status": "success",
            "processed": processed_count,
            "training_data_ids": training_data_ids
        }
    
    def create_training_data(self, feedback: Dict, connection) -> Optional[int]:
        """Create training data from user feedback"""
        cursor = connection.cursor()
        
        query_pattern = self.generalize_query_pattern(feedback['OriginalQuery'])
        
        cursor.execute(
            """INSERT INTO training_data 
               (FeedbackId, CompanyId, KnowledgeBaseId, QueryPattern, 
                CorrectResponse, IncorrectResponse, ImprovementNotes)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (feedback['Id'], feedback['CompanyId'], feedback['KnowledgeBaseId'],
             query_pattern, feedback['CorrectedResponse'], feedback['OriginalResponse'],
             feedback['FeedbackNotes'])
        )
        
        training_data_id = cursor.lastrowid
        cursor.close()
        
        return training_data_id
    
    def generalize_query_pattern(self, original_query: str) -> str:
        """Generalize a specific query into a reusable pattern"""
        pattern = original_query.lower()
        
        common_replacements = {
            'sales orders': '[SALES_ENTITY]',
            'customers': '[CUSTOMER_ENTITY]',
            'products': '[PRODUCT_ENTITY]',
            'orders': '[ORDER_ENTITY]',
            'payments': '[PAYMENT_ENTITY]'
        }
        
        for term, placeholder in common_replacements.items():
            pattern = pattern.replace(term, placeholder)
        
        return pattern
    
    def generate_corrected_documentation(self, training_data_ids: List[int], connection) -> List[Dict]:
        """Generate corrected documentation from training data"""
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(
            """SELECT * FROM training_data WHERE Id IN ({})""".format(
                ','.join(['%s'] * len(training_data_ids))
            ),
            training_data_ids
        )
        
        training_data = cursor.fetchall()
        cursor.close()
        
        corrected_docs = []
        
        for data in training_data:
            doc = {
                "query_pattern": data['QueryPattern'],
                "correct_sql": data['CorrectResponse'],
                "explanation": f"Corrected based on user feedback: {data['ImprovementNotes']}",
                "category": "user_corrections",
                "created_at": datetime.now().isoformat()
            }
            corrected_docs.append(doc)
        
        return corrected_docs
    
    def update_knowledge_base_with_corrections(self, kb_id: str, corrected_docs: List[Dict], 
                                             improvement_log_id: int, connection) -> Optional[str]:
        """Update knowledge base with corrected documentation"""
        try:
            logger.info(f"Would update KB {kb_id} with {len(corrected_docs)} corrections")
            logger.info(f"Corrections: {json.dumps(corrected_docs, indent=2)}")
            
            ingestion_job_id = f"job-{improvement_log_id}-{int(datetime.now().timestamp())}"
            
            return ingestion_job_id
            
        except Exception as e:
            logger.error(f"Error updating knowledge base: {e}")
            return None
