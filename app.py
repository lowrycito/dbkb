#!/usr/bin/env python3
"""
FastAPI application for Database Knowledge Base API
Migrated from serverless to ECS Fargate for better performance and reliability
"""

import os
import sys
import logging
import traceback
import time
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    mysql.connector = None
    Error = Exception

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

try:
    import uvicorn
except ImportError:
    uvicorn = None

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our retrieval utilities
from utils.retrieval import get_retrieval_client, format_response, validate_request

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dbkb_app')

# Global retrieval client - initialized once and reused
retrieval_client = None

# SSM client for parameter retrieval
ssm_client = None
cached_db_credentials = None

def get_ssm_client():
    """Get or create SSM client"""
    global ssm_client
    if not ssm_client and boto3:
        try:
            ssm_client = boto3.client('ssm')
        except Exception as e:
            logger.error(f"Failed to create SSM client: {e}")
    return ssm_client

def get_db_credentials():
    """Retrieve database credentials from SSM Parameter Store"""
    global cached_db_credentials
    
    # Return cached credentials if available
    if cached_db_credentials:
        return cached_db_credentials
    
    ssm = get_ssm_client()
    if not ssm:
        logger.warning("SSM client not available, using environment variables")
        cached_db_credentials = {
            'user': os.getenv('CHAT_DB_USER', 'chat_user'),
            'password': os.getenv('CHAT_DB_PASSWORD', '')
        }
        return cached_db_credentials
    
    try:
        # Retrieve credentials from SSM
        response = ssm.get_parameters(
            Names=[
                '/dbkb/chat/db/username',
                '/dbkb/chat/db/password'
            ],
            WithDecryption=True
        )
        
        credentials = {}
        for param in response['Parameters']:
            if param['Name'] == '/dbkb/chat/db/username':
                credentials['user'] = param['Value']
            elif param['Name'] == '/dbkb/chat/db/password':
                credentials['password'] = param['Value']
        
        # Fallback to environment variables if parameters not found
        if 'user' not in credentials:
            credentials['user'] = os.getenv('CHAT_DB_USER', 'chat_user')
            logger.warning("SSM parameter /dbkb/chat/db/username not found, using environment variable")
        
        if 'password' not in credentials:
            credentials['password'] = os.getenv('CHAT_DB_PASSWORD', '')
            logger.warning("SSM parameter /dbkb/chat/db/password not found, using environment variable")
        
        cached_db_credentials = credentials
        logger.info("Successfully retrieved database credentials from SSM")
        return credentials
        
    except ClientError as e:
        logger.error(f"Failed to retrieve SSM parameters: {e}")
        # Fallback to environment variables
        cached_db_credentials = {
            'user': os.getenv('CHAT_DB_USER', 'chat_user'),
            'password': os.getenv('CHAT_DB_PASSWORD', '')
        }
        return cached_db_credentials
    except Exception as e:
        logger.error(f"Unexpected error retrieving SSM parameters: {e}")
        # Fallback to environment variables
        cached_db_credentials = {
            'user': os.getenv('CHAT_DB_USER', 'chat_user'),
            'password': os.getenv('CHAT_DB_PASSWORD', '')
        }
        return cached_db_credentials

def get_chat_db_config():
    """Get database configuration with credentials from SSM"""
    credentials = get_db_credentials()
    return {
        'host': 'dev.writer.pic.picbusiness.aws',
        'database': 'chat',
        'user': credentials['user'],
        'password': credentials['password'],
        'port': int(os.getenv('CHAT_DB_PORT', 3306))
    }

def get_chat_db_connection():
    """Get database connection for chat persistence"""
    if not mysql.connector:
        logger.warning("MySQL connector not available - chat persistence disabled")
        return None
    
    try:
        db_config = get_chat_db_config()
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        logger.error(f"Failed to connect to chat database: {e}")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources on startup - simplified for fast startup"""
    global retrieval_client
    logger.info("Starting Database Knowledge Base API...")
    
    # Initialize to None first for fast startup
    retrieval_client = None
    logger.info("✅ API started successfully (client will be initialized on first request)")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Database Knowledge Base API...")

# Initialize FastAPI app
app = FastAPI(
    title="Database Knowledge Base API",
    description="Intelligent knowledge base for database schema and queries using Amazon Bedrock",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response - Base models first
class UserContext(BaseModel):
    loginId: str
    email: str
    firstName: str
    lastName: str
    company: str
    companyName: str
    industry: str
    databaseHost: str
    databaseSchema: str
    application: str  # epic, dis, ppd
    # KB IDs will be looked up from applications table

class ApplicationKBs(BaseModel):
    databaseKnowledgeBaseId: str
    supportKnowledgeBaseId: Optional[str] = None
    documentationKnowledgeBaseId: Optional[str] = None

class QueryTarget(BaseModel):
    type: str  # 'database', 'support', 'documentation'
    kbId: str
    secondary: Optional[bool] = False

class QueryRequest(BaseModel):
    query_text: str = Field(..., description="The query text to process")
    extended_thinking: bool = Field(True, description="Enable extended thinking mode")
    include_contexts: bool = Field(False, description="Include retrieved contexts in response")
    include_thinking: bool = Field(False, description="Include AI thinking process in response")
    userContext: Optional[UserContext] = None
    sessionId: Optional[str] = None
    queryTargets: Optional[List[QueryTarget]] = None
    queryMode: Optional[str] = 'smart'

class RelationshipRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to analyze relationships for")
    include_contexts: bool = Field(False, description="Include retrieved contexts in response")
    include_thinking: bool = Field(False, description="Include AI thinking process in response")
    userContext: Optional[UserContext] = None
    sessionId: Optional[str] = None
    queryTargets: Optional[List[QueryTarget]] = None
    queryMode: Optional[str] = 'smart'

class OptimizeRequest(BaseModel):
    sql_query: str = Field(..., description="SQL query to optimize")
    include_contexts: bool = Field(False, description="Include retrieved contexts in response")
    include_thinking: bool = Field(False, description="Include AI thinking process in response")
    userContext: Optional[UserContext] = None
    sessionId: Optional[str] = None
    queryTargets: Optional[List[QueryTarget]] = None
    queryMode: Optional[str] = 'smart'

class APIResponse(BaseModel):
    answer: str
    thinking: Optional[str] = None
    contexts: Optional[list] = None

class ChatSessionRequest(BaseModel):
    loginId: str
    email: str
    firstName: str
    lastName: str
    company: str
    companyName: str
    industry: str
    databaseHost: str
    databaseSchema: str
    application: str  # epic, dis, ppd

class ChatMessageRequest(BaseModel):
    sessionId: str
    messageType: str
    content: str
    metadata: Optional[Dict] = {}
    userContext: UserContext

class ChatSessionResponse(BaseModel):
    sessionId: str
    messages: Optional[List[Dict]] = []

class ChatMessage(BaseModel):
    Id: int
    MessageType: str
    Content: str
    CreatedAt: str
    Metadata: Optional[Dict] = {}

# Helper functions that use the models (moved after model definitions)
def get_application_kbs(application_name: str) -> Optional[ApplicationKBs]:
    """Get knowledge base IDs for an application"""
    connection = get_chat_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT DatabaseKnowledgeBaseId, SupportKnowledgeBaseId, DocumentationKnowledgeBaseId 
               FROM application WHERE Name = %s AND IsActive = TRUE""",
            (application_name,)
        )
        result = cursor.fetchone()
        
        if result:
            return ApplicationKBs(
                databaseKnowledgeBaseId=result['DatabaseKnowledgeBaseId'],
                supportKnowledgeBaseId=result['SupportKnowledgeBaseId'],
                documentationKnowledgeBaseId=result['DocumentationKnowledgeBaseId']
            )
        return None
        
    except Error as e:
        logger.error(f"Failed to get application KBs: {e}")
        return None
    finally:
        if connection:
            connection.close()

def classify_query_and_get_targets(query_text: str, app_kbs: ApplicationKBs, query_mode: str = 'smart') -> List[QueryTarget]:
    """Classify query and determine which knowledge bases to use"""
    targets = []
    
    if query_mode == 'database':
        # Force database KB only
        targets.append(QueryTarget(type='database', kbId=app_kbs.databaseKnowledgeBaseId))
    elif query_mode == 'support':
        # Force support KB only
        if app_kbs.supportKnowledgeBaseId:
            targets.append(QueryTarget(type='support', kbId=app_kbs.supportKnowledgeBaseId))
    elif query_mode == 'documentation':
        # Force documentation KB only
        if app_kbs.documentationKnowledgeBaseId:
            targets.append(QueryTarget(type='documentation', kbId=app_kbs.documentationKnowledgeBaseId))
    else:
        # Smart routing based on query classification
        query_lower = query_text.lower()
        
        # Database-related keywords
        db_keywords = ['table', 'column', 'database', 'sql', 'query', 'schema', 'index', 'foreign key', 'primary key', 'relationship', 'join']
        
        # Support-related keywords  
        support_keywords = ['error', 'issue', 'problem', 'troubleshoot', 'fix', 'bug', 'help', 'support', 'ticket', 'resolve']
        
        # Documentation-related keywords
        doc_keywords = ['how to', 'guide', 'tutorial', 'documentation', 'manual', 'instruction', 'feature', 'functionality']
        
        db_score = sum(1 for keyword in db_keywords if keyword in query_lower)
        support_score = sum(1 for keyword in support_keywords if keyword in query_lower)
        doc_score = sum(1 for keyword in doc_keywords if keyword in query_lower)
        
        # Determine primary target
        if db_score >= support_score and db_score >= doc_score:
            targets.append(QueryTarget(type='database', kbId=app_kbs.databaseKnowledgeBaseId))
        elif support_score > doc_score and app_kbs.supportKnowledgeBaseId:
            targets.append(QueryTarget(type='support', kbId=app_kbs.supportKnowledgeBaseId))
        elif app_kbs.documentationKnowledgeBaseId:
            targets.append(QueryTarget(type='documentation', kbId=app_kbs.documentationKnowledgeBaseId))
        else:
            # Default to database KB
            targets.append(QueryTarget(type='database', kbId=app_kbs.databaseKnowledgeBaseId))
    
    return targets

def ensure_user_and_company(user_context: UserContext):
    """Ensure user and company exist in database, create if needed"""
    connection = get_chat_db_connection()
    if not connection:
        return None, None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # First, get the application ID
        cursor.execute(
            "SELECT Id FROM application WHERE Name = %s AND IsActive = TRUE",
            (user_context.application,)
        )
        app_result = cursor.fetchone()
        
        if not app_result:
            logger.error(f"Application '{user_context.application}' not found")
            return None, None
        
        application_id = app_result['Id']
        
        # Check/create company
        cursor.execute(
            "SELECT Id FROM company WHERE CompanyCode = %s",
            (user_context.company,)
        )
        company_result = cursor.fetchone()
        
        if not company_result:
            cursor.execute(
                """INSERT INTO company (CompanyCode, CompanyName, Industry, 
                   DatabaseHost, DatabaseSchema, ApplicationId) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_context.company, user_context.companyName, user_context.industry,
                 user_context.databaseHost, user_context.databaseSchema, application_id)
            )
            company_id = cursor.lastrowid
        else:
            company_id = company_result['Id']
        
        # Check/create user
        cursor.execute(
            "SELECT Id FROM user WHERE LoginId = %s AND CompanyId = %s",
            (user_context.loginId, company_id)
        )
        user_result = cursor.fetchone()
        
        if not user_result:
            cursor.execute(
                """INSERT INTO user (LoginId, Email, FirstName, LastName, CompanyId) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_context.loginId, user_context.email, user_context.firstName, 
                 user_context.lastName, company_id)
            )
            user_id = cursor.lastrowid
        else:
            user_id = user_result['Id']
            # Update last active
            cursor.execute(
                "UPDATE user SET LastActiveAt = NOW() WHERE Id = %s",
                (user_id,)
            )
        
        connection.commit()
        return user_id, company_id
        
    except Error as e:
        logger.error(f"Database error in ensure_user_and_company: {e}")
        connection.rollback()
        return None, None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Mount static files for UI
try:
    app.mount("/static", StaticFiles(directory="src/ui"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Chat API endpoints
@app.post("/chat/session", response_model=ChatSessionResponse)
async def create_or_get_chat_session(request: ChatSessionRequest):
    """Create new chat session or get existing active session"""
    try:
        user_context = UserContext(**request.dict())
        user_id, company_id = ensure_user_and_company(user_context)
        
        if not user_id or not company_id:
            # Fallback - create session ID without database
            session_uuid = str(uuid.uuid4())
            return ChatSessionResponse(sessionId=session_uuid, messages=[])
        
        connection = get_chat_db_connection()
        if not connection:
            # Fallback - create session ID without database
            session_uuid = str(uuid.uuid4())
            return ChatSessionResponse(sessionId=session_uuid, messages=[])
        
        cursor = connection.cursor(dictionary=True)
        
        # Check for existing active session
        cursor.execute(
            """SELECT SessionUuid, Id FROM chat_sessions 
               WHERE UserId = %s AND CompanyId = %s AND IsActive = TRUE 
               ORDER BY CreatedAt DESC LIMIT 1""",
            (user_id, company_id)
        )
        session_result = cursor.fetchone()
        
        if session_result:
            session_uuid = session_result['SessionUuid']
            session_id = session_result['Id']
            
            # Get recent messages
            cursor.execute(
                """SELECT MessageType, Content, CreatedAt, Metadata 
                   FROM chat_messages 
                   WHERE SessionId = %s 
                   ORDER BY CreatedAt DESC LIMIT 50""",
                (session_id,)
            )
            messages = list(reversed(cursor.fetchall()))
        else:
            # Create new session
            session_uuid = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO chat_sessions (SessionUuid, UserId, CompanyId, KnowledgeBaseId) 
                   VALUES (%s, %s, %s, %s)""",
                (session_uuid, user_id, company_id, user_context.DatabaseKnowledgeBaseId)
            )
            connection.commit()
            messages = []
        
        cursor.close()
        connection.close()
        
        return ChatSessionResponse(sessionId=session_uuid, messages=messages)
        
    except Exception as e:
        logger.error(f"Error in create_or_get_chat_session: {e}")
        # Fallback - return session without database
        session_uuid = str(uuid.uuid4())
        return ChatSessionResponse(sessionId=session_uuid, messages=[])

def get_retrieval_client_for_kb(kb_id: str):
    """Get a retrieval client for a specific knowledge base ID"""
    try:
        # Import here to avoid circular imports
        from utils.retrieval import create_retrieval_client
        return create_retrieval_client(kb_id)
    except Exception as e:
        logger.error(f"Failed to create retrieval client for KB {kb_id}: {e}")
        return None

@app.post("/query/multi")
async def multi_kb_query(request: QueryRequest):
    """Query multiple knowledge bases based on application and routing configuration"""
    try:
        # Get query targets - either from request or determine from userContext
        if request.queryTargets and len(request.queryTargets) > 0:
            # Use explicitly provided targets
            targets = request.queryTargets
        elif request.userContext and request.userContext.application:
            # Get KB IDs for the application
            app_kbs = get_application_kbs(request.userContext.application)
            if not app_kbs:
                raise HTTPException(status_code=400, detail=f"Application '{request.userContext.application}' not found or has no knowledge bases configured")
            
            # Classify query and get appropriate targets
            targets = classify_query_and_get_targets(request.query_text, app_kbs, request.queryMode or 'smart')
        else:
            # Fallback to single KB query if no targets and no userContext
            return await query_knowledge_base(request)
        
        if not targets:
            raise HTTPException(status_code=400, detail="No knowledge base targets available for this query")
        
        results = []
        
        for target in targets:
            try:
                # Get retrieval client for this specific KB
                kb_client = get_retrieval_client_for_kb(target.kbId)
                if not kb_client:
                    logger.warning(f"Could not create client for KB {target.kbId}")
                    continue
                
                # Query this knowledge base
                result = kb_client.advanced_rag_query(
                    request.query_text,
                    use_extended_thinking=request.extended_thinking
                )
                
                result['source_type'] = target.type
                result['kb_id'] = target.kbId
                result['is_secondary'] = target.secondary or False
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error querying KB {target.kbId}: {e}")
                continue
        
        if not results:
            raise HTTPException(status_code=500, detail="No knowledge bases could be queried")
        
        # If only one result, return it directly
        if len(results) == 1:
            primary_result = results[0]
        else:
            # Merge results with primary/secondary priority
            primary_results = [r for r in results if not r.get('is_secondary', False)]
            secondary_results = [r for r in results if r.get('is_secondary', False)]
            
            if primary_results:
                primary_result = primary_results[0]
                
                # Append secondary information if available
                if secondary_results:
                    secondary_info = "\n\n**Related Information:**\n"
                    for secondary in secondary_results:
                        source_name = secondary['source_type'].title()
                        secondary_info += f"\n*From {source_name}:* {secondary['answer'][:200]}..."
                    
                    primary_result['answer'] += secondary_info
            else:
                primary_result = results[0]
        
        # Format response
        response_data = {"answer": primary_result['answer']}
        
        if request.include_thinking and primary_result.get('thinking'):
            response_data['thinking'] = primary_result['thinking']
        
        if request.include_contexts and primary_result.get('retrieved_contexts'):
            response_data['contexts'] = primary_result['retrieved_contexts']
        
        return APIResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error in multi-KB query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/message")
async def save_chat_message(request: ChatMessageRequest):
    """Save a chat message to the database"""
    try:
        user_id, company_id = ensure_user_and_company(request.userContext)
        
        if not user_id or not company_id:
            return {"status": "success", "note": "message not persisted - database unavailable"}
        
        connection = get_chat_db_connection()
        if not connection:
            return {"status": "success", "note": "message not persisted - database unavailable"}
        
        cursor = connection.cursor()
        
        # Get session internal ID
        cursor.execute(
            "SELECT Id FROM chat_sessions WHERE SessionUuid = %s",
            (request.sessionId,)
        )
        session_result = cursor.fetchone()
        
        if not session_result:
            cursor.close()
            connection.close()
            return {"status": "error", "message": "Session not found"}
        
        session_id = session_result[0]
        
        # Save message
        cursor.execute(
            """INSERT INTO chat_messages 
               (SessionId, UserId, CompanyId, MessageType, Content, Metadata, 
                QueryType, EndpointUsed, ResponseTimeMs) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (session_id, user_id, company_id, request.messageType, request.content,
             request.metadata.get('metadata', '{}') if request.metadata else '{}',
             request.metadata.get('queryType'), request.metadata.get('endpointUsed'),
             request.metadata.get('responseTime'))
        )
        
        # Update session timestamp
        cursor.execute(
            "UPDATE chat_sessions SET UpdatedAt = NOW() WHERE Id = %s",
            (session_id,)
        )
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {"status": "success", "message": "Message saved"}
        
    except Exception as e:
        logger.error(f"Error saving chat message: {e}")
        return {"status": "success", "note": "message not persisted - error occurred"}

@app.get("/db-knowledge-assistant.js")
async def serve_js():
    """Serve the JavaScript file directly"""
    try:
        with open("src/ui/db-knowledge-assistant.js", "r") as f:
            js_content = f.read()
        return HTMLResponse(content=js_content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="JavaScript file not found")

@app.get("/", response_class=HTMLResponse)
@app.get("/ui/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main UI page"""
    try:
        with open("src/ui/index.html", "r") as f:
            html_content = f.read()
        
        # Replace placeholder with actual API endpoint
        api_endpoint = os.getenv("API_ENDPOINT", "")
        html_content = html_content.replace("{{API_ENDPOINT}}", api_endpoint)
        
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>DBKB API</title></head>
            <body>
                <h1>Database Knowledge Base API</h1>
                <p>API is running. Access the documentation at <a href="/docs">/docs</a></p>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint for ECS Fargate and ALB"""
    try:
        # Simple health check that always returns healthy
        # Don't check complex dependencies during health check
        return {
            "status": "healthy",
            "service": "Database Knowledge Base API", 
            "version": "2.0.0",
            "timestamp": str(time.time())
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "healthy",  # Return healthy even on error
            "service": "Database Knowledge Base API",
            "version": "2.0.0", 
            "note": "simplified_health_check"
        }

@app.post("/query", response_model=APIResponse)
async def query_knowledge_base(request: QueryRequest):
    """General database knowledge base queries with multi-KB support"""
    try:
        # Check if this should be routed to multi-KB endpoint
        if request.queryTargets and len(request.queryTargets) > 0:
            return await multi_kb_query(request)
        
        # Single KB query (legacy/fallback behavior)
        global retrieval_client
        if not retrieval_client:
            try:
                logger.info("Initializing retrieval client on first request...")
                retrieval_client = get_retrieval_client()
                logger.info("✅ Retrieval client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize retrieval client: {e}")
                raise HTTPException(status_code=500, detail="Service initialization failed")

        logger.info(f"Processing single KB query: {request.query_text}")
        
        result = retrieval_client.advanced_rag_query(
            request.query_text, 
            use_extended_thinking=request.extended_thinking
        )

        # Format response based on options
        response_data = {"answer": result['answer']}

        if request.include_thinking and result.get('thinking'):
            response_data['thinking'] = result['thinking']

        if request.include_contexts and result.get('retrieved_contexts'):
            response_data['contexts'] = result['retrieved_contexts']

        return APIResponse(**response_data)

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/relationship", response_model=APIResponse)
async def analyze_table_relationships(request: RelationshipRequest):
    """Analyze relationships for a specific table"""
    try:
        # Lazy initialization of retrieval client
        global retrieval_client
        if not retrieval_client:
            try:
                logger.info("Initializing retrieval client on first request...")
                retrieval_client = get_retrieval_client()
                logger.info("✅ Retrieval client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize retrieval client: {e}")
                raise HTTPException(status_code=500, detail="Service initialization failed")

        logger.info(f"Analyzing relationships for table: {request.table_name}")
        
        result = retrieval_client.query_database_relationships(request.table_name)

        response_data = {"answer": result.get('relationship_analysis', '')}

        if request.include_thinking and result.get('thinking_process'):
            response_data['thinking'] = result['thinking_process']

        if request.include_contexts:
            response_data['contexts'] = result.get('retrieved_contexts', [])

        return APIResponse(**response_data)

    except Exception as e:
        logger.error(f"Error analyzing relationships: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize", response_model=APIResponse)
async def optimize_sql_query(request: OptimizeRequest):
    """Get optimization recommendations for a SQL query"""
    try:
        # Lazy initialization of retrieval client
        global retrieval_client
        if not retrieval_client:
            try:
                logger.info("Initializing retrieval client on first request...")
                retrieval_client = get_retrieval_client()
                logger.info("✅ Retrieval client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize retrieval client: {e}")
                raise HTTPException(status_code=500, detail="Service initialization failed")

        logger.info(f"Optimizing SQL query: {request.sql_query[:100]}...")
        
        # Create optimization query for the knowledge base
        optimization_query = f"How can I optimize this SQL query? {request.sql_query}"
        
        result = retrieval_client.advanced_rag_query(
            optimization_query, 
            use_extended_thinking=True
        )

        response_data = {"answer": result['answer']}

        if request.include_thinking and result.get('thinking'):
            response_data['thinking'] = result['thinking']

        if request.include_contexts and result.get('retrieved_contexts'):
            response_data['contexts'] = result['retrieved_contexts']

        return APIResponse(**response_data)

    except Exception as e:
        logger.error(f"Error optimizing query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    logger.info(f"Starting Database Knowledge Base API on {host}:{port}")
    
    if uvicorn:
        uvicorn.run(
            "app:app",
            host=host,
            port=port,
            log_level=log_level,
            reload=False,  # Disable reload in production
            access_log=True
        )
    else:
        logger.error("uvicorn not available. Install with: pip install uvicorn[standard]")
        sys.exit(1)
