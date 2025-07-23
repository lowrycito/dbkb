# Database Knowledge Base (DBKB) - Pipeline Documentation

## Overview

This document describes the complete data processing pipeline that creates and maintains the Database Knowledge Base used by the DBKB API. The pipeline extracts database schema information, analyzes SQL queries, generates documentation, and uploads content to Amazon Bedrock Knowledge Base.

## Pipeline Architecture

```
Database → Schema Extraction → Documentation Generation → S3 Upload → Bedrock Knowledge Base → API
    ↓
SQL Queries → Query Analysis → Markdown Generation → S3 Upload → Vector Embedding → Claude Analysis
```

## Components Overview

1. **Schema Extraction**: Extracts database metadata and relationships
2. **Query Analysis**: Analyzes SQL query patterns and generates documentation
3. **Documentation Generation**: Creates markdown files from extracted data
4. **S3 Upload**: Uploads documentation to S3 for Bedrock ingestion
5. **Knowledge Base Setup**: Configures Amazon Bedrock Knowledge Base
6. **Vector Indexing**: Bedrock creates vector embeddings for semantic search

## Main Pipeline Script

The main entry point is `main.py` which provides a CLI for running different pipeline stages:

```bash
python main.py [command] [options]
```

### Available Commands

- `extract-schema`: Extract database schema information
- `analyze-queries`: Analyze SQL query examples
- `generate-docs`: Generate documentation from schema and queries
- `upload`: Upload documentation to S3
- `setup-kb`: Set up Amazon Bedrock Knowledge Base
- `run-all`: Execute the entire pipeline

## 1. Schema Extraction (`src/schema_extraction/`)

### Purpose
Extracts comprehensive database schema information including tables, columns, relationships, indexes, and constraints.

### Key Files
- `extract_schema.py`: Main extraction logic
- `db_connection.py`: Database connection utilities
- `database.ini`: Database configuration file

### Configuration

Create `src/schema_extraction/database.ini`:

```ini
[postgresql]
host = your-host
port = 5432
database = your-database
user = your-username
password = your-password
schema = public
db_type = postgresql

[mysql]
host = your-host
port = 3306
database = your-database
user = your-username
password = your-password
schema = your-database
db_type = mysql
```

### Usage

```bash
# Extract PostgreSQL schema
python main.py extract-schema --section postgresql --output schema_data.json --generate-markdown

# Extract MySQL schema
python main.py extract-schema --section mysql --output schema_data.json --generate-markdown
```

### Output Format

The extraction generates `schema_data.json` with this structure:

```json
{
  "tables": {
    "table_name": {
      "name": "table_name",
      "description": "Table description",
      "columns": {
        "column_name": {
          "name": "column_name",
          "data_type": "varchar(255)",
          "is_nullable": false,
          "default": null,
          "description": "Column description",
          "is_primary_key": true,
          "foreign_key": {
            "table": "referenced_table",
            "column": "referenced_column",
            "constraint": "constraint_name"
          },
          "has_index": true
        }
      }
    }
  },
  "relationships": [
    {
      "source_table": "table1",
      "source_column": "column1",
      "target_table": "table2", 
      "target_column": "column2",
      "constraint_name": "fk_constraint"
    }
  ]
}
```

### Supported Database Types

- **PostgreSQL**: Full support for schemas, relationships, indexes
- **MySQL**: Full support with automatic schema detection
- **SQL Server**: Basic support (extensible)
- **Oracle**: Basic support (extensible)

## 2. Query Analysis (`src/query_analysis/`)

### Purpose
Analyzes SQL query examples to understand patterns, complexity, and usage, generating business-friendly documentation.

### Key Files
- `query_parser.py`: SQL query parsing and analysis logic

### Input Format

SQL queries are provided in a text file, one query per line:

```sql
SELECT * FROM users WHERE active = 1;
SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id;
-- More queries...
```

### Usage

```bash
# Analyze queries with schema context
python main.py analyze-queries --input queries.sql --output query_analysis.json --schema schema_data.json --generate-markdown

# Analyze without schema context
python main.py analyze-queries --input queries.sql --output query_analysis.json --generate-markdown
```

### Analysis Features

1. **Query Classification**: SELECT, INSERT, UPDATE, DELETE, DDL
2. **Complexity Scoring**: Based on joins, subqueries, aggregations
3. **Table Dependencies**: Identifies used tables and columns
4. **Join Analysis**: Analyzes relationship patterns
5. **Parameter Detection**: Identifies parameterized queries
6. **Performance Insights**: Identifies potential optimization opportunities

### Output Format

```json
[
  {
    "name": "query_001",
    "query_text": "SELECT ...",
    "query_type": "SELECT",
    "tables": ["users", "orders"],
    "columns": ["name", "total"],
    "joins": [
      {
        "type": "INNER JOIN",
        "left_table": "users",
        "right_table": "orders",
        "condition": "users.id = orders.user_id"
      }
    ],
    "complexity_score": 3,
    "parameters": ["?", "?"],
    "business_description": "Generated business description",
    "technical_description": "Technical query analysis"
  }
]
```

## 3. Documentation Generation

### Schema Documentation (`src/documentation/schema_to_markdown.py`)

Generates comprehensive markdown documentation from schema data:

- **Table summaries** with statistics
- **Detailed table documentation** for each table
- **Relationship diagrams** and explanations
- **Index and constraint information**
- **Cross-references** between related tables

### Generated Structure

```
docs/
├── schema/
│   ├── index.md                    # Schema overview
│   ├── tables/
│   │   ├── tables_summary.md       # All tables summary
│   │   ├── table1.md              # Individual table docs
│   │   └── table2.md
│   └── relationships/
│       └── relationships_summary.md # Relationship overview
```

### Query Documentation (`src/documentation/queries_to_markdown.py`)

Generates business-friendly documentation from query analysis:

- **Query categorization** by business function
- **Usage examples** with explanations
- **Performance recommendations**
- **Business impact** descriptions

### Generated Structure

```
docs/
├── queries/
│   ├── index.md                    # Query overview
│   ├── categories/
│   │   ├── reporting.md           # Reporting queries
│   │   ├── transactions.md        # Transaction queries
│   │   └── analytics.md           # Analytics queries
│   └── individual/
│       ├── query_001.md           # Individual query docs
│       └── query_002.md
```

### Usage

```bash
# Generate all documentation
python main.py generate-docs --schema schema_data.json --queries query_analysis.json --output-dir docs

# Generate only schema docs
python main.py generate-docs --schema schema_data.json --output-dir docs

# Generate only query docs
python main.py generate-docs --queries query_analysis.json --output-dir docs
```

## 4. S3 Upload (`src/bedrock_setup/upload_to_s3.py`)

### Purpose
Uploads generated documentation to S3 for Amazon Bedrock Knowledge Base ingestion.

### Key Features

- **Automatic bucket creation** if needed
- **Recursive file upload** with proper MIME types
- **Progress tracking** for large uploads
- **Error handling** and retry logic
- **Cleanup** of previous versions

### Usage

```bash
# Upload with automatic bucket creation
python main.py upload --bucket my-dbkb-bucket --prefix dbkb-docs --region us-east-1 --create-bucket

# Upload to existing bucket
python main.py upload --bucket existing-bucket --prefix knowledge-base --region us-east-1
```

### File Organization

```
s3://bucket/prefix/
├── schema/
│   ├── index.md
│   ├── tables/
│   │   └── *.md
│   └── relationships/
│       └── *.md
└── queries/
    ├── index.md
    └── *.md
```

## 5. Knowledge Base Setup (`src/bedrock_setup/setup_knowledge_base.py`)

### Purpose
Creates and configures Amazon Bedrock Knowledge Base with the uploaded documentation.

### Key Features

- **Knowledge Base creation** with optimal settings
- **Data source configuration** pointing to S3
- **Vector store setup** with appropriate chunking
- **Synchronization** and indexing
- **Test query execution** for validation

### Configuration Options

```python
{
    "name": "Database Knowledge Base",
    "description": "Intelligent database schema and query knowledge base",
    "embedding_model": "amazon.titan-embed-text-v1",
    "vector_store": "opensearch-serverless",
    "chunking_strategy": "fixed_size",
    "chunk_size": 300,
    "overlap": 20
}
```

### Usage

```bash
# Set up knowledge base with test query
python main.py setup-kb --bucket my-bucket --prefix dbkb-docs --region us-east-1 --name "DB Knowledge Base" --test-query "What tables are in the database?"
```

### Output

Creates `kb_info.json` with connection details:

```json
{
  "kb_id": "KRD3MW7QFS",
  "data_source_id": "ABC123",
  "name": "Database Knowledge Base",
  "description": "Database Schema Knowledge Base",
  "region": "us-east-1",
  "s3_bucket": "my-bucket",
  "s3_prefix": "dbkb-docs"
}
```

## 6. Complete Pipeline Execution

### Run All Command

```bash
python main.py run-all \
  --section postgresql \
  --queries queries.sql \
  --bucket dbkb-bucket \
  --prefix dbkb \
  --region us-east-1 \
  --kb-name "Production DB Knowledge Base" \
  --create-bucket
```

### Pipeline Steps

1. **Extract schema** from database
2. **Analyze queries** from input file
3. **Generate documentation** in markdown format
4. **Upload to S3** with proper organization
5. **Create Knowledge Base** and configure data source
6. **Sync and index** content
7. **Test** with sample query
8. **Save configuration** for future use

### Pipeline Monitoring

The pipeline provides detailed logging:

```
INFO:dbkb_main:Extracting schema information from database
INFO:dbkb_main:Schema data saved to schema_data.json
INFO:dbkb_main:Analyzing 150 queries
INFO:dbkb_main:Query analysis saved to query_analysis.json
INFO:dbkb_main:Generating documentation to docs/
INFO:dbkb_main:Schema documentation generated successfully
INFO:dbkb_main:Query documentation generated successfully
INFO:dbkb_main:Uploading documentation to s3://bucket/prefix/
INFO:dbkb_main:Documentation uploaded successfully
INFO:dbkb_main:Setting up knowledge base: DB Knowledge Base
INFO:dbkb_main:Knowledge base created successfully: KRD3MW7QFS
```

## Customization and Extension

### Adding New Database Types

1. **Extend schema extraction**:
   ```python
   # In extract_schema.py
   def extract_oracle_schema(connection_params):
       # Oracle-specific extraction logic
       pass
   ```

2. **Update configuration**:
   ```ini
   [oracle]
   host = oracle-host
   port = 1521
   database = XE
   user = username
   password = password
   schema = HR
   db_type = oracle
   ```

### Custom Query Analysis

1. **Add analysis functions**:
   ```python
   # In query_parser.py
   def analyze_custom_patterns(query):
       # Custom pattern analysis
       return patterns
   ```

2. **Extend output format**:
   ```python
   analysis_result.update({
       'custom_metrics': analyze_custom_patterns(query),
       'business_impact': assess_business_impact(query)
   })
   ```

### Custom Documentation Templates

1. **Create template files**:
   ```markdown
   # Custom Table Template
   
   ## {{ table.name }}
   
   **Purpose**: {{ table.business_purpose }}
   **Owner**: {{ table.owner }}
   **Last Updated**: {{ table.last_modified }}
   
   ### Custom Metrics
   - Record Count: {{ table.record_count }}
   - Growth Rate: {{ table.growth_rate }}
   ```

2. **Update generation logic**:
   ```python
   # In schema_to_markdown.py
   def generate_custom_table_doc(table_data, template):
       return template.render(table=table_data)
   ```

## Troubleshooting

### Common Issues

1. **Database Connection Failures**:
   ```bash
   # Test connection
   python -c "
   from src.schema_extraction.db_connection import test_connection
   test_connection('postgresql')
   "
   ```

2. **Large Schema Extraction**:
   ```python
   # Add progress tracking
   def extract_with_progress(tables):
       for i, table in enumerate(tables):
           print(f'Processing {i+1}/{len(tables)}: {table}')
           extract_table_info(table)
   ```

3. **S3 Upload Failures**:
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Test S3 access
   aws s3 ls s3://your-bucket/
   ```

4. **Knowledge Base Sync Issues**:
   ```bash
   # Check Bedrock service limits
   aws bedrock-agent list-knowledge-bases --region us-east-1
   
   # Monitor sync status
   aws bedrock-agent get-data-source --knowledge-base-id KRD3MW7QFS --data-source-id ABC123
   ```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

1. **Parallel Processing**:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   def parallel_table_extraction(tables):
       with ThreadPoolExecutor(max_workers=4) as executor:
           futures = [executor.submit(extract_table, table) for table in tables]
           return [future.result() for future in futures]
   ```

2. **Caching**:
   ```python
   import json
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def cached_query_analysis(query_hash):
       return analyze_query(query_hash)
   ```

## Maintenance and Updates

### Regular Maintenance

1. **Schema Updates**: Re-run extraction when database schema changes
2. **Query Analysis**: Add new query patterns as they emerge
3. **Documentation Updates**: Refresh documentation templates
4. **Knowledge Base Sync**: Periodic re-sync of content

### Automated Pipeline

Create a scheduled pipeline:

```bash
#!/bin/bash
# daily_update.sh

cd /path/to/dbkb
python main.py extract-schema --section production --output schema_data.json
python main.py analyze-queries --input new_queries.sql --output query_analysis.json --schema schema_data.json
python main.py upload --bucket prod-dbkb --prefix daily-$(date +%Y%m%d)
aws bedrock-agent start-ingestion-job --knowledge-base-id KRD3MW7QFS --data-source-id ABC123
```

### Version Control

Track pipeline configurations:

```json
{
  "pipeline_version": "2.0.0",
  "last_run": "2024-01-15T10:30:00Z",
  "schema_version": "1.2.3",
  "query_count": 245,
  "knowledge_base_id": "KRD3MW7QFS",
  "s3_location": "s3://bucket/prefix/"
}
```

## Integration with API

The generated knowledge base integrates seamlessly with the DBKB API:

1. **Vector Search**: API uses Bedrock's vector search capabilities
2. **Context Retrieval**: Multiple retrieval strategies access the knowledge base
3. **Response Generation**: Claude Sonnet 4 synthesizes responses from retrieved content
4. **Real-time Updates**: Knowledge base updates reflect in API responses

This comprehensive pipeline ensures that the Database Knowledge Base API has access to the most current, well-structured, and semantically rich information about your database systems.