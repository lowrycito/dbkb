#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import json
import configparser

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import project modules
from src.schema_extraction.extract_schema import extract_schema_to_json
from src.documentation.schema_to_markdown import generate_schema_documentation
from src.query_analysis.query_parser import analyze_query_batch
from src.documentation.queries_to_markdown import generate_markdown_from_json as generate_query_documentation
from src.bedrock_setup.upload_to_s3 import upload_documentation, create_bucket_if_not_exists
from src.bedrock_setup.setup_knowledge_base import create_and_configure_knowledge_base

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dbkb_main')

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Database Knowledge Base (DBKB) Pipeline',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('--config', default='database.ini',
                        help='Path to database configuration file (default: database.ini)')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    subparsers.required = True

    # Schema extraction parser
    schema_parser = subparsers.add_parser('extract-schema',
                                         help='Extract database schema information')
    schema_parser.add_argument('--section', default='postgresql',
                              help='Section name in the database.ini file (default: postgresql)')
    schema_parser.add_argument('--output', default='schema_data.json',
                              help='Output file path (default: schema_data.json)')
    schema_parser.add_argument('--generate-markdown', action='store_true',
                              help='Generate markdown documentation from schema')

    # Query analysis parser
    query_parser = subparsers.add_parser('analyze-queries',
                                        help='Analyze SQL query examples')
    query_parser.add_argument('--input', required=True,
                             help='Input file containing SQL queries (one per line)')
    query_parser.add_argument('--output', default='query_analysis.json',
                             help='Output file path (default: query_analysis.json)')
    query_parser.add_argument('--schema', default='schema_data.json',
                             help='Schema data JSON file (default: schema_data.json)')
    query_parser.add_argument('--generate-markdown', action='store_true',
                             help='Generate markdown documentation from query analysis')

    # Documentation generation parser
    docs_parser = subparsers.add_parser('generate-docs',
                                       help='Generate documentation from schema and/or query analysis')
    docs_parser.add_argument('--schema', default='schema_data.json',
                            help='Schema data JSON file (default: schema_data.json)')
    docs_parser.add_argument('--queries', default='query_analysis.json',
                            help='Query analysis JSON file (default: query_analysis.json)')
    docs_parser.add_argument('--output-dir', default='docs',
                            help='Output directory (default: docs)')

    # S3 upload parser
    upload_parser = subparsers.add_parser('upload',
                                         help='Upload documentation to S3')
    upload_parser.add_argument('--bucket', required=True,
                              help='S3 bucket name')
    upload_parser.add_argument('--prefix', default='dbkb',
                              help='Key prefix for S3 objects (default: dbkb)')
    upload_parser.add_argument('--region', default='us-east-1',
                              help='AWS region (default: us-east-1)')
    upload_parser.add_argument('--create-bucket', action='store_true',
                              help='Create S3 bucket if it does not exist')

    # Knowledge base setup parser
    kb_parser = subparsers.add_parser('setup-kb',
                                     help='Set up Amazon Bedrock Knowledge Base')
    kb_parser.add_argument('--bucket', required=True,
                          help='S3 bucket name containing documentation')
    kb_parser.add_argument('--prefix', default='dbkb',
                          help='Key prefix for documentation (default: dbkb)')
    kb_parser.add_argument('--region', default='us-east-1',
                          help='AWS region (default: us-east-1)')
    kb_parser.add_argument('--name', default='db-knowledge-base',
                          help='Knowledge base name (default: db-knowledge-base)')
    kb_parser.add_argument('--description', default='Database Schema Knowledge Base',
                          help='Knowledge base description')
    kb_parser.add_argument('--test-query',
                          help='Test query to run after setup')

    # Run all parser
    all_parser = subparsers.add_parser('run-all',
                                      help='Run the entire pipeline')
    all_parser.add_argument('--section', default='postgresql',
                           help='Section name in the database.ini file (default: postgresql)')
    all_parser.add_argument('--queries', required=True,
                           help='Input file containing SQL queries (one per line)')
    all_parser.add_argument('--bucket', required=True,
                           help='S3 bucket name')
    all_parser.add_argument('--prefix', default='dbkb',
                           help='Key prefix for S3 objects (default: dbkb)')
    all_parser.add_argument('--region', default='us-east-1',
                           help='AWS region (default: us-east-1)')
    all_parser.add_argument('--kb-name', default='db-knowledge-base',
                           help='Knowledge base name (default: db-knowledge-base)')
    all_parser.add_argument('--create-bucket', action='store_true',
                           help='Create S3 bucket if it does not exist')

    return parser.parse_args()

def run_extract_schema(args):
    """Run schema extraction command"""
    logger.info("Extracting schema information from database (config: %s, section: %s)", args.config, args.section)

    # Make sure config file exists
    if not os.path.exists(args.config):
        config_path = os.path.join('src', 'schema_extraction', args.config)
        if os.path.exists(config_path):
            args.config = config_path
        else:
            logger.error("Config file not found: %s", args.config)
            return False

    # Read DB connection info from config
    config = configparser.ConfigParser()
    config.read(args.config)
    if args.section not in config:
        logger.error("Section '%s' not found in config file: %s", args.section, args.config)
        return False
    section = config[args.section]
    host = section.get('host', 'localhost')
    port = section.get('port', '5432')
    dbname = section.get('database', '')
    user = section.get('user', '')
    password = section.get('password', '')
    schema = section.get('schema', 'public')
    db_type = section.get('db_type', args.section)

    # For MySQL, default schema to database name if not set
    if db_type.lower() == 'mysql' and not section.get('schema'):
        schema = dbname

    # Extract schema
    schema_data = extract_schema_to_json(host, port, dbname, user, password, schema, db_type)

    # Save to file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(schema_data, f, indent=2)

    logger.info("Schema data saved to %s", args.output)

    # Generate markdown documentation if requested
    if args.generate_markdown:
        output_dir = os.path.join('docs', 'schema')
        os.makedirs(output_dir, exist_ok=True)

        logger.info("Generating markdown documentation to %s", output_dir)
        result = generate_schema_documentation(args.output, output_dir)

        if result:
            logger.info("Schema documentation generated successfully")
        else:
            logger.error("Failed to generate schema documentation")
            return False

    return True

def run_analyze_queries(args):
    """Run query analysis command"""
    logger.info("Analyzing queries from %s", args.input)

    # Make sure input file exists
    if not os.path.exists(args.input):
        logger.error("Input file not found: %s", args.input)
        return False

    # Make sure schema file exists if provided
    schema_data = None
    if args.schema and os.path.exists(args.schema):
        with open(args.schema, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)

    # Read queries from input file
    with open(args.input, 'r', encoding='utf-8') as f:
        queries = [line.strip() for line in f if line.strip()]

    logger.info("Analyzing %d queries", len(queries))

    # Analyze queries
    analysis_results = analyze_query_batch(queries, schema_data)

    # Save to file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2)

    logger.info("Query analysis saved to %s", args.output)

    # Generate markdown documentation if requested
    if args.generate_markdown:
        output_dir = os.path.join('docs', 'queries')
        os.makedirs(output_dir, exist_ok=True)

        logger.info("Generating query documentation to %s", output_dir)
        result = generate_query_documentation(args.output, output_dir, args.schema)

        if result:
            logger.info("Query documentation generated successfully")
        else:
            logger.error("Failed to generate query documentation")
            return False

    return True

def run_generate_docs(args):
    """Run documentation generation command"""
    success = True

    # Generate schema documentation if schema file exists
    if os.path.exists(args.schema):
        schema_output_dir = os.path.join(args.output_dir, 'schema')
        os.makedirs(schema_output_dir, exist_ok=True)

        logger.info("Generating schema documentation to %s", schema_output_dir)
        schema_result = generate_schema_documentation(args.schema, schema_output_dir)

        if schema_result:
            logger.info("Schema documentation generated successfully")
        else:
            logger.error("Failed to generate schema documentation")
            success = False
    else:
        logger.warning("Schema file not found: %s", args.schema)

    # Generate query documentation if query analysis file exists
    if os.path.exists(args.queries):
        query_output_dir = os.path.join(args.output_dir, 'queries')
        os.makedirs(query_output_dir, exist_ok=True)

        logger.info("Generating query documentation to %s", query_output_dir)
        query_result = generate_query_documentation(args.queries, query_output_dir, args.schema)

        if query_result:
            logger.info("Query documentation generated successfully")
        else:
            logger.error("Failed to generate query documentation")
            success = False
    else:
        logger.warning("Query analysis file not found: %s", args.queries)

    return success

def run_upload(args):
    """Run upload command"""
    # Create bucket if requested
    if args.create_bucket:
        logger.info("Creating S3 bucket: %s", args.bucket)
        create_result = create_bucket_if_not_exists(args.bucket, args.region)

        if not create_result:
            logger.error("Failed to create or confirm bucket: %s", args.bucket)
            return False

    # Upload documentation
    logger.info("Uploading documentation to s3://%s/%s/", args.bucket, args.prefix)
    upload_result = upload_documentation(
        os.path.dirname(os.path.abspath(__file__)),
        args.bucket,
        args.prefix
    )

    if upload_result:
        logger.info("Documentation uploaded successfully")
    else:
        logger.error("Failed to upload documentation")
        return False

    return True

def run_setup_kb(args):
    """Run knowledge base setup command"""
    logger.info("Setting up knowledge base: %s", args.name)

    kb_id, ds_id = create_and_configure_knowledge_base(
        args.name,
        args.description,
        args.bucket,
        args.prefix,
        args.region,
        args.test_query
    )

    if kb_id:
        logger.info("Knowledge base created successfully: %s", kb_id)
        if ds_id:
            logger.info("Data source created successfully: %s", ds_id)

            # Save knowledge base info to file
            kb_info = {
                'kb_id': kb_id,
                'data_source_id': ds_id,
                'name': args.name,
                'description': args.description,
                'region': args.region,
                's3_bucket': args.bucket,
                's3_prefix': args.prefix
            }

            with open('kb_info.json', 'w', encoding='utf-8') as f:
                json.dump(kb_info, f, indent=2)

            logger.info("Knowledge base info saved to kb_info.json")
        else:
            logger.error("Failed to create data source")
            return False
    else:
        logger.error("Failed to create knowledge base")
        return False

    return True

def run_all(args):
    """Run the entire pipeline"""
    # 1. Extract schema
    schema_args = argparse.Namespace(
        config=args.section,
        section=args.section,
        output='schema_data.json',
        generate_markdown=True
    )

    if not run_extract_schema(schema_args):
        return False

    # 2. Analyze queries
    query_args = argparse.Namespace(
        input=args.queries,
        output='query_analysis.json',
        schema='schema_data.json',
        generate_markdown=True
    )

    if not run_analyze_queries(query_args):
        return False

    # 3. Upload documentation to S3
    upload_args = argparse.Namespace(
        bucket=args.bucket,
        prefix=args.prefix,
        region=args.region,
        create_bucket=args.create_bucket
    )

    if not run_upload(upload_args):
        return False

    # 4. Set up knowledge base
    kb_args = argparse.Namespace(
        bucket=args.bucket,
        prefix=args.prefix,
        region=args.region,
        name=args.kb_name,
        description='Database Schema Knowledge Base',
        test_query='What tables does the database have?'
    )

    if not run_setup_kb(kb_args):
        return False

    return True

def main():
    """Main entry point"""
    args = parse_args()

    try:
        if args.command == 'extract-schema':
            success = run_extract_schema(args)
        elif args.command == 'analyze-queries':
            success = run_analyze_queries(args)
        elif args.command == 'generate-docs':
            success = run_generate_docs(args)
        elif args.command == 'upload':
            success = run_upload(args)
        elif args.command == 'setup-kb':
            success = run_setup_kb(args)
        elif args.command == 'run-all':
            success = run_all(args)
        else:
            logger.error("Unknown command: %s", args.command)
            return 1

        if success:
            logger.info("Command '%s' completed successfully", args.command)
            return 0
        else:
            logger.error("Command '%s' failed", args.command)
            return 1

    except Exception as e:
        logger.exception("Error running command '%s': %s", args.command, e)
        return 1

if __name__ == '__main__':
    sys.exit(main())