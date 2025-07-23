-- Aurora MySQL Database Schema for Chat History and User Context
-- Database: chat on dev.writer.pic.picbusiness.aws

CREATE DATABASE IF NOT EXISTS chat;
USE chat;

-- Application table - represents industry packages (epic, dis, ppd) with their knowledge bases
CREATE TABLE application (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL UNIQUE,
    DisplayName VARCHAR(100) NOT NULL,
    Description TEXT,
    DatabaseKnowledgeBaseId VARCHAR(255) NOT NULL,
    SupportKnowledgeBaseId VARCHAR(255),
    DocumentationKnowledgeBaseId VARCHAR(255),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    IsActive BOOLEAN DEFAULT TRUE,
    
    INDEX idx_application_name (Name),
    INDEX idx_db_knowledge_base_id (DatabaseKnowledgeBaseId),
    INDEX idx_support_knowledge_base_id (SupportKnowledgeBaseId),
    INDEX idx_doc_knowledge_base_id (DocumentationKnowledgeBaseId)
);

-- Company table - represents each customer organization
CREATE TABLE company (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    CompanyCode VARCHAR(50) NOT NULL UNIQUE,
    CompanyName VARCHAR(255) NOT NULL,
    Industry VARCHAR(100),
    DatabaseHost VARCHAR(255) NOT NULL,
    DatabaseSchema VARCHAR(100) NOT NULL,
    ApplicationId INT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    IsActive BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (ApplicationId) REFERENCES application(Id),
    INDEX idx_company_code (CompanyCode),
    INDEX idx_application_id (ApplicationId)
);

-- User table - represents users from customer systems
CREATE TABLE user (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    LoginId VARCHAR(100) NOT NULL,
    Email VARCHAR(255) NOT NULL,
    FirstName VARCHAR(100),
    LastName VARCHAR(100),
    CompanyId INT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    LastActiveAt TIMESTAMP NULL,
    IsActive BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (CompanyId) REFERENCES company(Id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_per_company (LoginId, CompanyId),
    INDEX idx_email (Email),
    INDEX idx_company_user (CompanyId, LoginId)
);

-- Chat session - groups related messages together
CREATE TABLE chat_session (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    SessionUuid CHAR(36) NOT NULL UNIQUE,
    UserId INT NOT NULL,
    CompanyId INT NOT NULL,
    KnowledgeBaseId VARCHAR(255) NOT NULL,
    Title VARCHAR(255),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    EndedAt TIMESTAMP NULL,
    IsActive BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (UserId) REFERENCES user(Id) ON DELETE CASCADE,
    FOREIGN KEY (CompanyId) REFERENCES company(Id) ON DELETE CASCADE,
    INDEX idx_session_uuid (SessionUuid),
    INDEX idx_user_sessions (UserId, CreatedAt DESC),
    INDEX idx_company_sessions (CompanyId, CreatedAt DESC),
    INDEX idx_knowledge_base (KnowledgeBaseId)
);

-- Chat message - individual messages within sessions
CREATE TABLE chat_message (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    SessionId INT NOT NULL,
    UserId INT NOT NULL,
    CompanyId INT NOT NULL,
    MessageType ENUM('user', 'assistant', 'system') NOT NULL,
    Content TEXT NOT NULL,
    QueryType VARCHAR(50),  -- 'general', 'relationship', 'optimization'
    EndpointUsed VARCHAR(100), -- '/query', '/relationship', '/optimize'
    ResponseTimeMs INT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    QueryMode VARCHAR(20), -- 'smart', 'database', 'support', 'documentation'
    KnowledgeBasesUsed JSON, -- Array of KB IDs that were queried
    SourceKnowledgeBase VARCHAR(255), -- Primary KB that provided the answer
    Metadata JSON, -- Store additional context like thinking process, contexts, etc.
    
    FOREIGN KEY (SessionId) REFERENCES chat_session(Id) ON DELETE CASCADE,
    FOREIGN KEY (UserId) REFERENCES user(Id) ON DELETE CASCADE,
    FOREIGN KEY (CompanyId) REFERENCES company(Id) ON DELETE CASCADE,
    INDEX idx_session_messages (SessionId, CreatedAt),
    INDEX idx_user_messages (UserId, CreatedAt DESC),
    INDEX idx_company_messages (CompanyId, CreatedAt DESC),
    INDEX idx_message_type (MessageType)
);

-- Query analytic - track popular queries and performance
CREATE TABLE query_analytic (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    CompanyId INT NOT NULL,
    KnowledgeBaseId VARCHAR(255) NOT NULL,
    QueryText TEXT NOT NULL,
    QueryHash VARCHAR(64) NOT NULL, -- MD5 hash for deduplication
    QueryType VARCHAR(50),
    EndpointUsed VARCHAR(100),
    ResponseTimeMs INT,
    Success BOOLEAN DEFAULT TRUE,
    ErrorMessage TEXT,
    UsageCount INT DEFAULT 1,
    FirstUsedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastUsedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (CompanyId) REFERENCES company(Id) ON DELETE CASCADE,
    UNIQUE KEY unique_query_per_company (CompanyId, QueryHash),
    INDEX idx_company_analytics (CompanyId, LastUsedAt DESC),
    INDEX idx_knowledge_base_analytics (KnowledgeBaseId),
    INDEX idx_query_performance (ResponseTimeMs),
    INDEX idx_popular_queries (UsageCount DESC)
);

-- User preference - store user-specific settings
CREATE TABLE user_preference (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    PreferenceKey VARCHAR(100) NOT NULL,
    PreferenceValue TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (UserId) REFERENCES user(Id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_preference (UserId, PreferenceKey)
);

-- Sample data for testing

-- Insert application packages with their knowledge base IDs
INSERT INTO application (Name, DisplayName, Description, DatabaseKnowledgeBaseId, SupportKnowledgeBaseId, DocumentationKnowledgeBaseId) VALUES
('epic', 'Epic EMR', 'Electronic Medical Records system for healthcare organizations', 'KB-EPIC-DB-001', 'KB-EPIC-SUPPORT-001', 'KB-EPIC-DOCS-001'),
('dis', 'DIS System', 'Distribution and inventory management system', 'KB-DIS-DB-002', 'KB-DIS-SUPPORT-002', 'KB-DIS-DOCS-002'),
('ppd', 'PPD Platform', 'Project planning and delivery management platform', 'KB-PPD-DB-003', 'KB-PPD-SUPPORT-003', 'KB-PPD-DOCS-003');

-- Insert companies that use these application packages
INSERT INTO company (CompanyCode, CompanyName, Industry, DatabaseHost, DatabaseSchema, ApplicationId) VALUES
('HOSPITAL001', 'General Hospital', 'Healthcare', 'hospital-db.cluster-xyz.us-east-1.rds.amazonaws.com', 'epic_prod', 1),
('CLINIC002', 'City Clinic', 'Healthcare', 'clinic-db.cluster-abc.us-east-1.rds.amazonaws.com', 'epic_main', 1),
('WAREHOUSE003', 'Distribution Co', 'Logistics', 'warehouse-db.cluster-def.us-east-1.rds.amazonaws.com', 'dis_prod', 2),
('CONSTRUCTION004', 'BuildCorp Inc', 'Construction', 'build-db.cluster-ghi.us-east-1.rds.amazonaws.com', 'ppd_main', 3);

-- Sample users
INSERT INTO user (LoginId, Email, FirstName, LastName, CompanyId) VALUES
('dr.smith', 'dr.smith@generalhospital.com', 'John', 'Smith', 1),
('nurse.jones', 'mary.jones@cityclinic.com', 'Mary', 'Jones', 2),
('manager.davis', 'bob.davis@distributionco.com', 'Bob', 'Davis', 3),
('pm.wilson', 'alice.wilson@buildcorp.com', 'Alice', 'Wilson', 4);