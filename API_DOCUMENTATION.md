# Database Knowledge Base (DBKB) - API Documentation

## Overview

The Database Knowledge Base API provides intelligent querying capabilities for database schemas and SQL queries using Amazon Bedrock and Claude Sonnet 4. The API processes natural language queries and returns comprehensive, structured responses about database structures, relationships, and best practices.

**Base URL**: `https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/`

## API Features

- **Intelligent Query Processing**: Natural language understanding of database-related questions
- **Multi-Strategy Retrieval**: Combines standard, query expansion, and HyDE retrieval techniques
- **Claude Sonnet 4 Integration**: Advanced AI analysis with cross-region inference
- **Structured Responses**: Well-formatted, actionable information
- **Context-Aware**: Maintains awareness of database schema and relationships

## Authentication

The API currently does not require authentication for basic usage. All endpoints are publicly accessible.

## Rate Limiting

No explicit rate limiting is implemented, but underlying AWS Bedrock service limits apply.

## API Endpoints

### 1. Health Check

**GET** `/health`

Returns the health status of the API service.

#### Response

```json
{
  "status": "healthy",
  "service": "Database Knowledge Base API",
  "version": "2.0.0",
  "timestamp": "1748044327.8622515"
}
```

#### Example

```bash
curl -k "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/health"
```

---

### 2. General Query

**POST** `/query`

Processes natural language queries about the database and returns intelligent responses.

#### Request Body

```json
{
  "query_text": "string",
  "extended_thinking": true,
  "include_contexts": false,
  "include_thinking": false
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query_text` | string | Yes | - | The natural language query about the database |
| `extended_thinking` | boolean | No | true | Enable extended AI thinking process |
| `include_contexts` | boolean | No | false | Include retrieved document contexts in response |
| `include_thinking` | boolean | No | false | Include AI thinking process in response |

#### Response

```json
{
  "answer": "string",
  "thinking": "string or null",
  "contexts": ["array of strings or null"]
}
```

#### Example Request

```bash
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "what tables are in this database?",
    "extended_thinking": false,
    "include_contexts": false,
    "include_thinking": false
  }'
```

#### Example Response

```json
{
  "answer": "Based on the documentation provided, I can help you understand how to find the tables in your database...\n\n## How to View Database Tables\n\nThere are two main SQL queries you can use...",
  "thinking": null,
  "contexts": null
}
```

#### Common Query Types

- **Schema Discovery**: "what tables are in this database?", "show me the database structure"
- **Relationship Analysis**: "what are the relationships between tables?", "how do these tables connect?"
- **Query Optimization**: "how can I optimize this SQL query?", "what indexes should I create?"
- **Business Logic**: "what is this database used for?", "explain the business purpose of these tables"

---

### 3. Table Relationships

**POST** `/relationship`

Analyzes relationships for a specific table in the database.

#### Request Body

```json
{
  "table_name": "string",
  "include_contexts": false,
  "include_thinking": false
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `table_name` | string | Yes | - | Name of the table to analyze relationships for |
| `include_contexts` | boolean | No | false | Include retrieved document contexts in response |
| `include_thinking` | boolean | No | false | Include AI thinking process in response |

#### Response

```json
{
  "answer": "string",
  "thinking": "string or null",
  "contexts": ["array of strings or null"]
}
```

#### Example Request

```bash
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/relationship" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "db_order",
    "include_contexts": false,
    "include_thinking": false
  }'
```

---

### 4. SQL Query Optimization

**POST** `/optimize`

Provides optimization recommendations for SQL queries based on database schema knowledge.

#### Request Body

```json
{
  "sql_query": "string",
  "include_contexts": false,
  "include_thinking": false
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sql_query` | string | Yes | - | The SQL query to optimize |
| `include_contexts` | boolean | No | false | Include retrieved document contexts in response |
| `include_thinking` | boolean | No | false | Include AI thinking process in response |

#### Response

```json
{
  "answer": "string",
  "thinking": "string or null", 
  "contexts": ["array of strings or null"]
}
```

#### Example Request

```bash
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "sql_query": "SELECT * FROM users WHERE created_date > '\''2023-01-01'\''",
    "include_contexts": false,
    "include_thinking": false
  }'
```

---

### 5. Web Interface

**GET** `/`

Serves the interactive web interface for the Database Knowledge Base.

#### Response

Returns an HTML page with a user-friendly interface for querying the database knowledge base.

#### Features

- Interactive query input
- Real-time response display
- Query history
- Example queries
- Response formatting

---

### 6. API Documentation

**GET** `/docs`

Interactive API documentation using Swagger UI.

**GET** `/redoc`

Alternative API documentation using ReDoc.

## Response Format Details

### Success Response Structure

All successful API responses follow this structure:

```json
{
  "answer": "Main response content with formatted markdown",
  "thinking": "AI thinking process (if requested)",
  "contexts": ["Retrieved document contexts (if requested)"]
}
```

### Error Response Structure

```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

### Common HTTP Status Codes

- **200**: Success
- **400**: Bad Request (invalid input)
- **422**: Validation Error (malformed request body)
- **500**: Internal Server Error

## Advanced Features

### Multi-Strategy Retrieval

The API uses three retrieval strategies simultaneously:

1. **Standard Retrieval**: Direct semantic search in the knowledge base
2. **Query Expansion**: Generates multiple query variations for comprehensive results
3. **HyDE (Hypothetical Document Embedding)**: Creates hypothetical answers to improve retrieval

### Claude Sonnet 4 Integration

- **Model**: `us.anthropic.claude-sonnet-4-20250514-v1:0`
- **Cross-Region Inference**: Improved availability and performance
- **Context Window**: Large context for comprehensive analysis
- **Structured Output**: Markdown-formatted responses

### Knowledge Base Content

The knowledge base contains:
- Database schema information
- Table relationships and constraints
- Query examples and patterns
- Business logic documentation
- Performance optimization guidelines

## Client Libraries and SDKs

### Python Example

```python
import requests
import json

def query_dbkb(query_text, include_thinking=False):
    url = "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query"
    payload = {
        "query_text": query_text,
        "extended_thinking": True,
        "include_contexts": False,
        "include_thinking": include_thinking
    }
    
    response = requests.post(url, json=payload, verify=False)
    return response.json()

# Example usage
result = query_dbkb("what are the main table categories?")
print(result["answer"])
```

### JavaScript Example

```javascript
async function queryDBKB(queryText, includeThinking = false) {
    const url = 'https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query';
    const payload = {
        query_text: queryText,
        extended_thinking: true,
        include_contexts: false,
        include_thinking: includeThinking
    };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        return await response.json();
    } catch (error) {
        console.error('Error querying DBKB:', error);
        throw error;
    }
}

// Example usage
queryDBKB('describe the database structure').then(result => {
    console.log(result.answer);
});
```

### cURL Examples

#### Basic Query
```bash
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "what tables are in this database?"}'
```

#### Query with Full Context
```bash
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "explain the EDI processing workflow",
    "extended_thinking": true,
    "include_contexts": true,
    "include_thinking": true
  }'
```

#### Table Relationship Analysis
```bash
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/relationship" \
  -H "Content-Type: application/json" \
  -d '{"table_name": "db_customer"}'
```

## Best Practices

### Query Optimization

1. **Be Specific**: More specific queries yield better results
   - Good: "What are the foreign key relationships for the db_order table?"
   - Better: "Show me how db_order connects to other tables through foreign keys"

2. **Use Business Context**: Include business context for better understanding
   - Good: "What tables store customer data?"
   - Better: "What tables store customer information and how is customer data organized?"

3. **Ask for Examples**: Request examples when learning about the schema
   - "Show me example queries for retrieving order information"

### Performance Considerations

1. **Batch Related Queries**: Group related questions when possible
2. **Use Caching**: Implement client-side caching for repeated queries
3. **Monitor Response Times**: Track API response times for performance

### Error Handling

```python
def safe_query_dbkb(query_text):
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}
```

## Monitoring and Debugging

### Health Monitoring

```bash
# Check API health
curl -k "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/health"

# Monitor response time
time curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "test query"}'
```

### Debug Mode

Include thinking and contexts for debugging:

```json
{
  "query_text": "your question",
  "extended_thinking": true,
  "include_contexts": true,
  "include_thinking": true
}
```

## Limitations

1. **Context Window**: Very large database schemas may exceed context limits
2. **Rate Limits**: Subject to underlying AWS Bedrock service limits
3. **Language Support**: Optimized for English queries
4. **Real-time Data**: Knowledge base reflects static schema information

## Support and Troubleshooting

### Common Issues

1. **SSL Certificate Warnings**: Use `-k` flag with curl or disable SSL verification
2. **Timeout Errors**: Increase client timeout for complex queries
3. **Empty Responses**: Check query spelling and ensure knowledge base coverage

### Getting Help

1. Check the `/docs` endpoint for interactive documentation
2. Review CloudWatch logs for detailed error information
3. Use the web interface at `/` for user-friendly querying
4. Test with the `/health` endpoint to verify service availability

### Version Information

- **API Version**: 2.0.0
- **Claude Model**: Sonnet 4 (us.anthropic.claude-sonnet-4-20250514-v1:0)
- **Knowledge Base**: Static database schema documentation
- **Last Updated**: Current deployment timestamp available at `/health`