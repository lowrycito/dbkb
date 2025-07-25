# Feedback Collection and Training System

## Overview

The feedback system allows users to correct incorrect SQL responses from the knowledge base and automatically improves the system over time through machine learning. This system captures user corrections, processes them into training data, and updates the knowledge base to provide better responses.

## Database Schema

The feedback system extends the chat database with three new tables:

### query_feedback
Stores user corrections, ratings, and improvement suggestions for assistant responses.

```sql
CREATE TABLE query_feedback (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    MessageId INT NOT NULL,           -- References chat_message.Id
    UserId INT NOT NULL,
    CompanyId INT NOT NULL,
    SessionId INT NOT NULL,
    
    -- Feedback details
    FeedbackType ENUM('correction', 'rating', 'improvement_suggestion') NOT NULL,
    Rating INT NULL,                  -- 1-5 star rating
    OriginalQuery TEXT NOT NULL,      -- User's original question
    OriginalResponse TEXT NOT NULL,   -- Assistant's incorrect response
    CorrectedResponse TEXT NULL,      -- User's corrected response
    FeedbackNotes TEXT NULL,          -- Additional comments
    
    -- Classification
    ProblemCategory VARCHAR(100) NULL, -- 'wrong_table', 'syntax_error', etc.
    KnowledgeBaseId VARCHAR(255) NOT NULL,
    
    -- Processing status
    ProcessingStatus ENUM('pending', 'reviewed', 'applied', 'rejected') DEFAULT 'pending',
    ProcessedAt TIMESTAMP NULL,
    ProcessedBy VARCHAR(100) NULL,
    
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### training_data
Processes feedback into generalized training examples for knowledge base improvements.

```sql
CREATE TABLE training_data (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    FeedbackId INT NOT NULL,          -- References query_feedback.Id
    CompanyId INT NOT NULL,
    KnowledgeBaseId VARCHAR(255) NOT NULL,
    
    -- Training content
    QueryPattern TEXT NOT NULL,       -- Generalized query pattern
    CorrectResponse TEXT NOT NULL,    -- Correct SQL response
    IncorrectResponse TEXT NOT NULL,  -- Original incorrect response
    ImprovementNotes TEXT NULL,       -- What was wrong and how fixed
    
    -- Training metadata
    TrainingWeight DECIMAL(3,2) DEFAULT 1.0,
    ValidationStatus ENUM('pending', 'validated', 'rejected') DEFAULT 'pending',
    
    -- Usage tracking
    TimesUsed INT DEFAULT 0,
    LastUsedAt TIMESTAMP NULL,
    
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### kb_improvement_log
Tracks knowledge base improvements and their results.

```sql
CREATE TABLE kb_improvement_log (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    KnowledgeBaseId VARCHAR(255) NOT NULL,
    CompanyId INT NOT NULL,
    
    -- Improvement details
    ImprovementType ENUM('content_update', 'prompt_refinement', 'schema_correction') NOT NULL,
    Description TEXT NOT NULL,
    TrainingDataIds JSON,             -- Array of training_data.Id values
    
    -- Implementation
    ImplementationMethod ENUM('ingestion_job', 'prompt_update', 'manual_review') NOT NULL,
    IngestionJobId VARCHAR(255) NULL, -- AWS Bedrock job ID
    Status ENUM('planned', 'in_progress', 'completed', 'failed') DEFAULT 'planned',
    
    -- Results
    SuccessMetrics JSON NULL,
    ErrorDetails TEXT NULL,
    
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CompletedAt TIMESTAMP NULL
);
```

## API Endpoints

### Submit Feedback
**POST /feedback**

Submit feedback for an assistant response that was incorrect or needs improvement.

```json
{
    "messageId": 123,
    "sessionId": "session-uuid",
    "feedbackType": "correction",
    "rating": 2,
    "originalQuery": "Show me all sales orders by payment date",
    "originalResponse": "SELECT * FROM db_salescommissionlog WHERE...",
    "correctedResponse": "SELECT * FROM db_order WHERE DatePaid != '0000-00-00' ORDER BY DatePaid",
    "feedbackNotes": "Used wrong table - should be db_order not db_salescommissionlog",
    "problemCategory": "wrong_table",
    "userContext": {
        "loginId": "user.name",
        "email": "user@company.com",
        "company": "COMP001",
        "application": "epic"
    }
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Feedback submitted successfully",
    "feedbackId": 456
}
```

### Check Training Status
**GET /feedback/training-status**

Get the current training status for a knowledge base.

**Parameters:**
- `knowledgeBaseId`: Knowledge base ID (e.g., "KRD3MW7QFS")
- `userContext`: User context object

**Response:**
```json
{
    "pendingFeedback": 5,
    "processedFeedback": 23,
    "lastTrainingUpdate": "2024-01-15T10:30:00Z",
    "improvementMetrics": {
        "accuracy_improvement": "12%",
        "corrections_applied": 15
    }
}
```

### Process Training Pipeline
**POST /feedback/process-training**

Trigger the training pipeline to process pending feedback and update the knowledge base.

```json
{
    "knowledgeBaseId": "KRD3MW7QFS",
    "userContext": {
        "loginId": "admin.user",
        "company": "COMP001"
    }
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Processed 5 feedback items",
    "details": {
        "status": "success",
        "processed": 5,
        "training_data_ids": [101, 102, 103, 104, 105]
    }
}
```

## Training Pipeline

### Automatic Processing
The training pipeline automatically processes user feedback through these steps:

1. **Feedback Collection**: User submits correction via API or UI widget
2. **Pattern Generalization**: Convert specific queries into reusable patterns
3. **Training Data Creation**: Store generalized corrections for future use
4. **Knowledge Base Update**: Apply corrections to improve future responses
5. **Validation**: Track success metrics and improvement results

### Manual Processing
Use the CLI tool to manually process feedback:

```bash
# Check pending feedback (dry run)
python train_from_feedback.py --kb-id KRD3MW7QFS --company-id 1 --dry-run

# Process all pending feedback
python train_from_feedback.py --kb-id KRD3MW7QFS --company-id 1
```

### CLI Tool Options
- `--kb-id`: Knowledge base ID to process (required)
- `--company-id`: Company ID for filtering feedback (required)
- `--dry-run`: Show what would be processed without making changes

## UI Integration

### Feedback Widget
Include the feedback widget in your chat interface:

```html
<script src="src/ui/feedback-widget.js"></script>
<script>
const feedbackWidget = new FeedbackWidget('http://your-api-endpoint');

// Show feedback form for a message
feedbackWidget.showFeedbackForm(
    messageId,
    sessionId,
    originalQuery,
    originalResponse,
    userContext
);
</script>
```

### Widget Features
- 1-5 star rating system
- Problem categorization (wrong table, syntax error, etc.)
- Correction text area for improved SQL
- Additional notes for explanations
- Automatic submission to feedback API

## Monitoring and Analytics

### Feedback Metrics
Track feedback collection and processing:

```sql
-- Pending feedback count
SELECT COUNT(*) FROM query_feedback 
WHERE ProcessingStatus = 'pending' AND KnowledgeBaseId = 'KRD3MW7QFS';

-- Feedback by problem category
SELECT ProblemCategory, COUNT(*) as count 
FROM query_feedback 
WHERE KnowledgeBaseId = 'KRD3MW7QFS' 
GROUP BY ProblemCategory;

-- Training data usage
SELECT QueryPattern, TimesUsed, LastUsedAt 
FROM training_data 
WHERE KnowledgeBaseId = 'KRD3MW7QFS' 
ORDER BY TimesUsed DESC;
```

### Improvement Tracking
Monitor knowledge base improvements:

```sql
-- Recent improvements
SELECT * FROM kb_improvement_log 
WHERE KnowledgeBaseId = 'KRD3MW7QFS' 
ORDER BY CreatedAt DESC LIMIT 10;

-- Success metrics
SELECT ImprovementType, Status, SuccessMetrics 
FROM kb_improvement_log 
WHERE Status = 'completed' AND KnowledgeBaseId = 'KRD3MW7QFS';
```

## Best Practices

### Feedback Collection
1. **Immediate Feedback**: Collect feedback right after incorrect responses
2. **Specific Corrections**: Encourage users to provide exact SQL corrections
3. **Problem Categorization**: Use consistent categories for better analysis
4. **Context Preservation**: Always include original query and response

### Training Pipeline
1. **Regular Processing**: Run training pipeline weekly or when feedback accumulates
2. **Validation**: Review training data before applying to knowledge base
3. **Monitoring**: Track improvement metrics and success rates
4. **Rollback Plan**: Keep logs for reverting problematic updates

### Quality Control
1. **Review Corrections**: Validate user corrections before applying
2. **Pattern Analysis**: Look for common error patterns to address systematically
3. **Performance Tracking**: Monitor query accuracy improvements over time
4. **User Education**: Provide feedback on how corrections are being used

## Troubleshooting

### Common Issues

**Foreign Key Constraint Errors**
- Ensure valid MessageId, UserId, CompanyId, and SessionId exist
- Check that referenced records haven't been deleted

**Training Pipeline Failures**
- Verify AWS credentials and Bedrock permissions
- Check knowledge base accessibility and status
- Review error logs in kb_improvement_log table

**No Feedback Being Collected**
- Verify API endpoints are accessible
- Check user context and authentication
- Ensure database connections are working

### Debug Commands

```bash
# Test feedback system components
python test_feedback_endpoints.py

# Test imports and basic functionality
python test_imports.py

# Check database connectivity
python -c "from app import get_chat_db_connection; print('DB OK' if get_chat_db_connection() else 'DB FAIL')"
```

## Integration with Knowledge Bases

### Database KB (KRD3MW7QFS)
- Focused on SQL query generation
- Learns from table/column corrections
- Improves JOIN and WHERE clause accuracy

### Support KB (ECC3L7C2PG)
- Customer support interactions
- Zendesk article suggestions
- Ticket history analysis

The feedback system works with both knowledge bases, automatically routing corrections to the appropriate KB based on the query context and knowledge base ID.

## Multi-Knowledge Base Integration

### Database KB (KRD3MW7QFS)
- **Purpose**: SQL query generation and database schema assistance
- **Feedback Focus**: Table/column corrections, JOIN accuracy, WHERE clause improvements
- **Training Pipeline**: Processes corrections into SQL pattern improvements

### Support KB (ECC3L7C2PG)  
- **Purpose**: Customer support interactions and ticket history analysis
- **Feedback Focus**: Solution accuracy, escalation appropriateness, article suggestions
- **Training Pipeline**: Improves support response quality and ticket routing

### Retraining Workflows

#### Automated Retraining
The system automatically processes feedback weekly:

```bash
# Automated weekly retraining (add to cron)
0 2 * * 0 cd /path/to/dbkb && python train_from_feedback.py --kb-id KRD3MW7QFS --company-id 1
0 3 * * 0 cd /path/to/dbkb && python train_from_feedback.py --kb-id ECC3L7C2PG --company-id 1
```

#### Manual Retraining
For immediate improvements after critical feedback:

```bash
# Process database KB feedback
python train_from_feedback.py --kb-id KRD3MW7QFS --company-id [your-company-id]

# Process support KB feedback  
python train_from_feedback.py --kb-id ECC3L7C2PG --company-id [your-company-id]

# Dry run to see what would be processed
python train_from_feedback.py --kb-id KRD3MW7QFS --company-id [your-company-id] --dry-run
```

#### Monitoring Training Effectiveness

```bash
# Check training status via API
curl -X GET "http://your-api/feedback/training-status?knowledgeBaseId=KRD3MW7QFS&userContext={...}"

# View improvement metrics
SELECT ImprovementType, Status, SuccessMetrics 
FROM kb_improvement_log 
WHERE KnowledgeBaseId = 'KRD3MW7QFS' AND Status = 'completed'
ORDER BY CreatedAt DESC;
```

### Query Routing and Feedback

The system automatically routes feedback to the appropriate knowledge base:
- **Database queries** → KRD3MW7QFS feedback collection
- **Support queries** → ECC3L7C2PG feedback collection  
- **Smart mode** → Routes based on query classification

This ensures feedback improves the correct knowledge base and maintains specialized expertise in each domain.

## Application Configuration

### Setting Up Knowledge Base IDs

Update the application table with your actual knowledge base IDs:

```bash
# Run the configuration update script
python update_application_kbs.py
```

Or manually update the database:

```sql
-- Update Epic application with actual KB IDs
UPDATE application 
SET DatabaseKnowledgeBaseId = 'KRD3MW7QFS', 
    SupportKnowledgeBaseId = 'ECC3L7C2PG',
    UpdatedAt = NOW()
WHERE Name = 'epic' AND IsActive = TRUE;
```

### Testing Multi-KB Routing

```bash
# Test query routing functionality
python test_multi_kb_routing.py

# Test specific query modes
curl -X POST "http://localhost:8000/query/multi" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Show me database tables",
    "queryMode": "database",
    "userContext": {...}
  }'
```

## UI Integration for Support

### Support History Viewing
The UI widget automatically shows support history when in support mode:

```javascript
// Switch to support mode to see history
widget.setQueryMode('support');
```

### Escalation to Human Support
Users can escalate to human support through the UI:

```javascript
// Show escalation options
widget.showEscalationOptions();
```

### Support-Specific Features
- **Support History**: View recent support sessions and queries
- **Ticket Creation**: Create Zendesk tickets (placeholder implementation)
- **Live Chat**: Initiate live chat with support (placeholder implementation)
- **Query Mode Selection**: Choose between database, support, and documentation modes

## Adding Additional Knowledge Bases

To add new knowledge bases to the system:

1. **Update Application Table**:
```sql
-- Add new application with KB IDs
INSERT INTO application (Name, DisplayName, Description, DatabaseKnowledgeBaseId, SupportKnowledgeBaseId, DocumentationKnowledgeBaseId) 
VALUES ('new_app', 'New Application', 'Description', 'KB-NEW-DB-001', 'KB-NEW-SUPPORT-001', 'KB-NEW-DOCS-001');
```

2. **Update Query Classification**:
Add new keywords to the classification logic in `app.py`:

```python
# Add application-specific keywords
new_app_keywords = ['new_app_term', 'specific_feature', 'custom_module']
```

3. **Configure UI**:
Update the UI widget to support the new application:

```javascript
// Add new query mode option
const queryModes = ['smart', 'database', 'support', 'documentation', 'new_app'];
```

4. **Test Integration**:
```bash
# Test new KB routing
python test_multi_kb_routing.py
```

The system is designed to scale to multiple knowledge bases while maintaining proper routing and feedback collection for each domain.
