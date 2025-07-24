# Database Knowledge Base (DBKB)

<!-- Verification test comment added by Devin -->

An intelligent knowledge base system for database schema documentation and query analysis using Amazon Bedrock with advanced RAG techniques.

## Overview

DBKB automates the process of extracting database schema information, analyzing SQL queries, generating comprehensive documentation, and making this knowledge accessible through a Claude 3.7 Sonnet powered knowledge base with advanced retrieval techniques.

**Note:** As of May 2025, DBKB supports both MySQL and PostgreSQL for schema extraction. MySQL is now the primary supported source for schema extraction, while PostgreSQL is used for the vector index.

### Key Features

- **Automated Schema Extraction**: Extract table structure, column definitions, relationships, and indexes from PostgreSQL databases.
- **Query Analysis**: Analyze patterns in SQL queries to identify common access patterns and usage examples.
- **Documentation Generation**: Create markdown documentation optimized for semantic chunking.
- **Amazon Bedrock Integration**: Set up a knowledge base with optimal chunking using Cohere Embed English.
- **Advanced RAG Techniques**: Implements multiple RAG strategies including:
  - Hypothetical Document Embeddings (HyDE)
  - Multi-query retrieval
  - Query expansion
  - AI-based reranking
- **Embeddable UI Component**: Web component that can be embedded in any web application.
- **AWS ECS Fargate API**: Scalable containerized API for querying the knowledge base with specialized endpoints for relationship analysis and query optimization.

## Architecture

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  PostgreSQL DB  │──▶│ Schema Extractor │──▶│    Markdown     │
└─────────────────┘   └─────────────────┘   │  Documentation   │
                                           │   Generation     │
┌─────────────────┐   ┌─────────────────┐   │                 │
│  Query Examples │──▶│  Query Analyzer  │──▶│                 │
└─────────────────┘   └─────────────────┘   └────────┬────────┘
                                                    │
                                                    ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Embeddable    │◀──│  AWS ECS Fargate │◀──│  Amazon Bedrock  │
│  UI Component   │   │   FastAPI App    │   │  Knowledge Base  │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- AWS Account with access to Amazon Bedrock
- MySQL or PostgreSQL database (for schema extraction)
- Pulumi CLI (for infrastructure deployment)
- Docker (for containerization)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/dbkb.git
   cd dbkb
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   # Create and activate a virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # OR
   .venv\Scripts\activate  # On Windows

   # Install dependencies
   pip install -r requirements.txt
   ```

3. Install Pulumi (for infrastructure):
   ```bash
   cd infrastructure
   pip install -r requirements.txt
   ```

## Configuration

### Database Connection

Create a `database.ini` file in the `src/schema_extraction` directory with your database connection details. Example for MySQL:

```ini
[mysql]
host=localhost
database=yourdb
user=youruser
password=yourpassword
port=3306
```

Example for PostgreSQL (for vector index):

```ini
[postgresql]
host=localhost
database=yourvectordb
user=youruser
password=yourpassword
port=5432
```

### AWS Configuration

Make sure your AWS credentials are configured:

```bash
aws configure
```

## Usage

Before running any commands, make sure you've activated your virtual environment:
```bash
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows
```

### Running the Complete Pipeline

To run the entire pipeline in one command:

```bash
python main.py run-all --queries path/to/query/examples.txt --bucket your-s3-bucket-name
```

### Running Individual Components

#### 1. Extract Schema Information

```bash
python main.py extract-schema --section mysql --generate-markdown
```

#### 2. Analyze SQL Queries

```bash
python main.py analyze-queries --input path/to/queries.txt --generate-markdown
```

#### 3. Generate Documentation

```bash
python main.py generate-docs --schema schema_data.json --queries query_analysis.json
```

#### 4. Upload Documentation to S3

```bash
python main.py upload --bucket your-s3-bucket-name --create-bucket
```

#### 5. Setup Knowledge Base

```bash
python main.py setup-kb --bucket your-s3-bucket-name --name your-kb-name
```

### Deploying to AWS ECS Fargate

#### Using GitHub Actions (Recommended)

1. Set up repository secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY` 
   - `PULUMI_ACCESS_TOKEN`

2. Push to main branch - deployment is automatic!

#### Manual Deployment

```bash
cd infrastructure
pulumi login
pulumi stack init prod
pulumi config set knowledge-base-id your-kb-id
pulumi up
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Using the Web Component

The UI is automatically served at the root of your ECS Fargate deployment. You can also embed the component in other applications:

```html
<script src="https://your-alb-domain.com/static/db-knowledge-assistant.js"></script>

<db-knowledge-assistant api-endpoint="https://your-alb-domain.com"></db-knowledge-assistant>
```

### Testing the Deployment

Once deployed, test your API:

```bash
# Health check
curl https://your-alb-domain.com/health

# Query the knowledge base
curl -X POST -H "Content-Type: application/json" \
  -d '{"query_text":"What tables are in the database?"}' \
  https://your-alb-domain.com/query
```

## Advanced RAG Techniques

This project implements several advanced Retrieval Augmented Generation (RAG) techniques:

### 1. Hypothetical Document Embeddings (HyDE)

For schema-related queries, the system generates a hypothetical document that would be a perfect answer to the query, then uses this document as the retrieval query. This helps bridge the semantic gap between the query and relevant documents.

### 2. Multi-Query Retrieval

The system expands the original user query into multiple alternative formulations, retrieves results for each, then merges and deduplicates them. This improves recall by capturing different aspects of the query.

### 3. AI-Based Reranking

Claude 3.7 Sonnet is used to rerank the retrieved documents based on their relevance to the query, which improves precision beyond vector similarity matching alone.

### 4. Extended Thinking with Claude 3.7

The system uses Claude's extended thinking capability to show a detailed reasoning process for complex queries, improving transparency and accuracy.

## Migration from Serverless

If you're upgrading from the old serverless Lambda deployment, see [MIGRATION.md](MIGRATION.md) for detailed migration instructions.

## Project Structure

```
dbkb/
├── app.py                    # FastAPI application (main entry point)
├── Dockerfile               # Container definition for ECS Fargate
├── requirements.txt         # Python dependencies
├── infrastructure/          # Pulumi infrastructure as code
│   ├── __main__.py          # Infrastructure definition
│   ├── Pulumi.yaml          # Pulumi project configuration
│   └── requirements.txt     # Pulumi dependencies
├── src/                     # Core application modules
│   ├── advanced_retrieval/  # RAG implementation
│   ├── bedrock_setup/       # Knowledge base setup utilities
│   ├── documentation/       # Documentation generators
│   ├── query_analysis/      # Query parsing and analysis
│   ├── schema_extraction/   # Database schema extraction
│   └── ui/                  # Web UI components
├── utils/                   # Shared utilities
├── .github/workflows/       # GitHub Actions for CI/CD
├── DEPLOYMENT.md           # Deployment guide
├── MIGRATION.md            # Migration guide from serverless
└── docs/                   # Generated documentation
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `python test_local_app.py`
5. Submit a pull request

### Deployment Pipeline

- **Pull Requests**: Automatically tested and deployed to preview environment
- **Main Branch**: Automatically deployed to production ECS Fargate service
- **Infrastructure Changes**: Managed through Pulumi in the `infrastructure/` directory
