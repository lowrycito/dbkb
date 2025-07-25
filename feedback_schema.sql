
USE chat;

CREATE TABLE query_feedback (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    MessageId INT NOT NULL, -- References chat_message.Id for the assistant response
    UserId INT NOT NULL,
    CompanyId INT NOT NULL,
    SessionId INT NOT NULL,
    
    FeedbackType ENUM('correction', 'rating', 'improvement_suggestion') NOT NULL,
    Rating INT NULL, -- 1-5 star rating for response quality
    OriginalQuery TEXT NOT NULL, -- The user's original question
    OriginalResponse TEXT NOT NULL, -- The assistant's response that was incorrect
    CorrectedResponse TEXT NULL, -- User's corrected/improved response
    FeedbackNotes TEXT NULL, -- Additional user comments
    
    ProblemCategory VARCHAR(100) NULL, -- 'wrong_table', 'syntax_error', 'missing_where_clause', etc.
    KnowledgeBaseId VARCHAR(255) NOT NULL, -- Which KB provided the incorrect response
    
    ProcessingStatus ENUM('pending', 'reviewed', 'applied', 'rejected') DEFAULT 'pending',
    ProcessedAt TIMESTAMP NULL,
    ProcessedBy VARCHAR(100) NULL, -- Admin/system that processed the feedback
    
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (MessageId) REFERENCES chat_message(Id) ON DELETE CASCADE,
    FOREIGN KEY (UserId) REFERENCES user(Id) ON DELETE CASCADE,
    FOREIGN KEY (CompanyId) REFERENCES company(Id) ON DELETE CASCADE,
    FOREIGN KEY (SessionId) REFERENCES chat_session(Id) ON DELETE CASCADE,
    
    INDEX idx_message_feedback (MessageId),
    INDEX idx_user_feedback (UserId, CreatedAt DESC),
    INDEX idx_company_feedback (CompanyId, CreatedAt DESC),
    INDEX idx_kb_feedback (KnowledgeBaseId, ProcessingStatus),
    INDEX idx_feedback_type (FeedbackType),
    INDEX idx_processing_status (ProcessingStatus, CreatedAt)
);

CREATE TABLE training_data (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    FeedbackId INT NOT NULL, -- References query_feedback.Id
    CompanyId INT NOT NULL,
    KnowledgeBaseId VARCHAR(255) NOT NULL,
    
    QueryPattern TEXT NOT NULL, -- Generalized query pattern
    CorrectResponse TEXT NOT NULL, -- The correct SQL response
    IncorrectResponse TEXT NOT NULL, -- The original incorrect response
    ImprovementNotes TEXT NULL, -- What was wrong and how it was fixed
    
    TrainingWeight DECIMAL(3,2) DEFAULT 1.0, -- Weight for this training example
    ValidationStatus ENUM('pending', 'validated', 'rejected') DEFAULT 'pending',
    
    TimesUsed INT DEFAULT 0, -- How many times this correction has been applied
    LastUsedAt TIMESTAMP NULL,
    
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (FeedbackId) REFERENCES query_feedback(Id) ON DELETE CASCADE,
    FOREIGN KEY (CompanyId) REFERENCES company(Id) ON DELETE CASCADE,
    
    INDEX idx_kb_training (KnowledgeBaseId, ValidationStatus),
    INDEX idx_company_training (CompanyId),
    INDEX idx_query_pattern (QueryPattern(255)),
    INDEX idx_validation_status (ValidationStatus)
);

CREATE TABLE kb_improvement_log (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    KnowledgeBaseId VARCHAR(255) NOT NULL,
    CompanyId INT NOT NULL,
    
    ImprovementType ENUM('content_update', 'prompt_refinement', 'schema_correction') NOT NULL,
    Description TEXT NOT NULL,
    TrainingDataIds JSON, -- Array of training_data.Id values used
    
    ImplementationMethod ENUM('ingestion_job', 'prompt_update', 'manual_review') NOT NULL,
    IngestionJobId VARCHAR(255) NULL, -- AWS Bedrock ingestion job ID if applicable
    Status ENUM('planned', 'in_progress', 'completed', 'failed') DEFAULT 'planned',
    
    SuccessMetrics JSON NULL, -- Performance improvements, accuracy gains, etc.
    ErrorDetails TEXT NULL,
    
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CompletedAt TIMESTAMP NULL,
    
    FOREIGN KEY (CompanyId) REFERENCES company(Id) ON DELETE CASCADE,
    
    INDEX idx_kb_improvements (KnowledgeBaseId, Status),
    INDEX idx_company_improvements (CompanyId, CreatedAt DESC),
    INDEX idx_improvement_type (ImprovementType),
    INDEX idx_status (Status, CreatedAt)
);

-- Sample data for testing
INSERT INTO query_feedback (MessageId, UserId, CompanyId, SessionId, FeedbackType, Rating, OriginalQuery, OriginalResponse, CorrectedResponse, FeedbackNotes, ProblemCategory, KnowledgeBaseId) VALUES
(1, 1, 1, 1, 'correction', 2, 'Show me all sales orders by payment date', 'SELECT * FROM db_salescommissionlog WHERE...', 'SELECT * FROM db_order WHERE DatePaid != "0000-00-00" ORDER BY DatePaid', 'Used wrong table - should be db_order not db_salescommissionlog', 'wrong_table', 'KRD3MW7QFS');
