import os
import json
import logging
import pandas as pd
import sqlparse
from sqlglot import parse as sqlglot_parse, exp
from sql_metadata import Parser as SQLMetadataParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('query_parser')

class QueryAnalyzer:
    """Analyzes SQL queries using multiple parsing libraries for robustness"""

    def __init__(self, schema_data=None):
        self.schema_data = schema_data

    def analyze_query(self, query_text, query_name=None):
        """Analyze a SQL query and extract metadata"""
        if not query_text:
            return None

        # Basic clean-up
        query_text = query_text.strip()

        # Initialize the result
        result = {
            'name': query_name or 'Unnamed Query',
            'query_text': query_text,
            'query_type': None,
            'tables': [],
            'columns': [],
            'joins': [],
            'where_conditions': [],
            'complexity': None,
            'formatted_query': None
        }

        try:
            # Parse with sqlparse to get query type and format
            parsed = sqlparse.parse(query_text)
            if parsed:
                stmt = parsed[0]
                result['query_type'] = stmt.get_type()
                result['formatted_query'] = sqlparse.format(
                    query_text,
                    reindent=True,
                    keyword_case='upper'
                )

            # Use sqlglot for detailed structure analysis
            try:
                sqlglot_result = self._analyze_with_sqlglot(query_text)
                result.update(sqlglot_result)
            except Exception as e:
                logger.warning(f"sqlglot parsing failed: {str(e)}")

            # Fallback/additional parsing with sql_metadata
            try:
                metadata_result = self._analyze_with_sql_metadata(query_text)

                # Only use sql_metadata results if sqlglot didn't find tables
                if not result['tables'] and metadata_result.get('tables'):
                    result['tables'] = metadata_result.get('tables')

                # Always merge columns from both parsers
                if metadata_result.get('columns'):
                    result['columns'].extend(
                        [col for col in metadata_result.get('columns') if col not in result['columns']]
                    )
            except Exception as e:
                logger.warning(f"sql_metadata parsing failed: {str(e)}")

            # Compute complexity
            result['complexity'] = self._compute_complexity(result)

            return result

        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            # Return partial results if available
            result['error'] = str(e)
            return result

    def _analyze_with_sqlglot(self, query_text):
        """Parse query using sqlglot for detailed structure"""
        result = {
            'tables': [],
            'columns': [],
            'joins': [],
            'where_conditions': []
        }

        try:
            parsed = sqlglot_parse(query_text)

            for statement in parsed:
                # Extract tables
                for table in statement.find_all(exp.Table):
                    if hasattr(table, 'name') and table.name not in result['tables']:
                        result['tables'].append(table.name)

                # Extract joins
                for join in statement.find_all(exp.Join):
                    join_info = {'type': 'JOIN'}

                    if hasattr(join, 'kind'):
                        join_info['kind'] = join.kind

                    if hasattr(join, 'this') and hasattr(join.this, 'name'):
                        join_info['table'] = join.this.name

                    if join_info not in result['joins']:
                        result['joins'].append(join_info)

                # Extract columns
                for column in statement.find_all(exp.Column):
                    if hasattr(column, 'name') and column.name not in result['columns']:
                        result['columns'].append(column.name)

                # Extract conditions
                for condition in statement.find_all(exp.Condition):
                    if hasattr(condition, 'left') and hasattr(condition.left, 'name'):
                        condition_info = {
                            'column': condition.left.name,
                            'operator': condition.op if hasattr(condition, 'op') else '?'
                        }
                        if condition_info not in result['where_conditions']:
                            result['where_conditions'].append(condition_info)

            return result
        except Exception as e:
            logger.warning(f"sqlglot detailed parsing failed: {str(e)}")
            return result

    def _analyze_with_sql_metadata(self, query_text):
        """Parse query using sql_metadata library"""
        result = {
            'tables': [],
            'columns': []
        }

        try:
            parser = SQLMetadataParser(query_text)

            # Extract tables
            tables = parser.tables
            if tables:
                result['tables'] = tables

            # Extract columns
            columns = parser.columns_dict
            if columns:
                for table, cols in columns.items():
                    result['columns'].extend(cols)

            return result
        except Exception as e:
            logger.warning(f"sql_metadata parsing failed: {str(e)}")
            return result

    def _compute_complexity(self, query_info):
        """Compute query complexity based on various factors"""
        complexity = 0

        # Base complexity
        if query_info['query_type'] == 'SELECT':
            complexity += 1
        elif query_info['query_type'] in ('INSERT', 'UPDATE', 'DELETE'):
            complexity += 2

        # Tables complexity
        complexity += len(query_info['tables']) * 0.5

        # Joins complexity
        complexity += len(query_info['joins']) * 1.5

        # Conditions complexity
        complexity += len(query_info['where_conditions']) * 0.5

        # Text complexity
        query_length = len(query_info['query_text'])
        if query_length > 1000:
            complexity += 2
        elif query_length > 500:
            complexity += 1

        # Classify complexity
        if complexity > 8:
            return 'High'
        elif complexity > 4:
            return 'Medium'
        else:
            return 'Low'


def analyze_query_batch(queries, schema_data=None):
    """Analyze a batch of queries"""
    analyzer = QueryAnalyzer(schema_data)
    results = []

    for i, (query_name, query_text) in enumerate(queries):
        logger.info(f"Analyzing query {i+1}/{len(queries)}: {query_name}")
        result = analyzer.analyze_query(query_text, query_name)
        results.append(result)

    return results


def process_query_file(input_file, output_file=None, schema_file=None):
    """Process a file containing queries and save analysis results"""
    schema_data = None

    # Load schema data if provided
    if schema_file and os.path.exists(schema_file):
        try:
            with open(schema_file, 'r') as f:
                schema_data = json.load(f)
            logger.info(f"Loaded schema data from {schema_file}")
        except Exception as e:
            logger.error(f"Error loading schema data: {str(e)}")

    # Determine output file if not specified
    if not output_file:
        base_dir = os.path.dirname(input_file)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(base_dir, f"{base_name}_analysis.json")

    # Read queries from file
    queries = []
    try:
        # Check file extension to determine format
        ext = os.path.splitext(input_file)[1].lower()

        if ext == '.json':
            # JSON format
            with open(input_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'name' in item and 'query' in item:
                            queries.append((item['name'], item['query']))
                        else:
                            logger.warning("Invalid query item format in JSON")
                else:
                    logger.error("JSON file should contain a list of query objects")

        elif ext in ('.csv', '.xlsx'):
            # CSV or Excel format
            if ext == '.csv':
                df = pd.read_csv(input_file)
            else:
                df = pd.read_excel(input_file)

            # Check for required columns
            if 'name' in df.columns and 'query' in df.columns:
                for _, row in df.iterrows():
                    queries.append((row['name'], row['query']))
            else:
                logger.error("CSV/Excel file should have 'name' and 'query' columns")

        else:
            # Plain text format (one query per file)
            with open(input_file, 'r') as f:
                query_text = f.read()
                queries.append((os.path.basename(input_file), query_text))

        logger.info(f"Loaded {len(queries)} queries from {input_file}")

        # Analyze queries
        results = analyze_query_batch(queries, schema_data)

        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Analysis results saved to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error processing queries: {str(e)}")
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Analyze SQL queries')
    parser.add_argument('input_file', help='Path to input file containing queries')
    parser.add_argument('--output', '-o', help='Path to output file for analysis results')
    parser.add_argument('--schema', '-s', help='Path to schema data JSON file')

    args = parser.parse_args()

    if process_query_file(args.input_file, args.output, args.schema):
        print("Query analysis completed successfully")
    else:
        print("Query analysis failed")