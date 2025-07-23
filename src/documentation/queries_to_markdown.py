import os
import sys
import json
import logging
import argparse
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('queries_to_markdown')

class QueryMarkdownGenerator:
    """Generate markdown documentation from analyzed SQL queries"""

    def __init__(self, queries_data, out_dir, schema_data=None):
        """Initialize with query data and output directory

        :param queries_data: Dictionary containing analyzed queries information
        :param out_dir: Directory to output markdown files
        :param schema_data: Optional schema data to enrich documentation
        """
        self.queries_data = queries_data
        self.schema_data = schema_data
        self.output_dir = out_dir

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Create subdirectories
        self.patterns_dir = os.path.join(self.output_dir, 'query_patterns')
        os.makedirs(self.patterns_dir, exist_ok=True)

        self.tables_dir = os.path.join(self.output_dir, 'tables_usage')
        os.makedirs(self.tables_dir, exist_ok=True)

    def generate_all_docs(self):
        """Generate all markdown documentation files"""
        logger.info("Starting query markdown generation")

        # Generate index file
        self.generate_index_file()

        # Generate query patterns
        self.generate_query_patterns()

        # Generate table usage documentation
        self.generate_tables_usage_docs()

        logger.info("Query markdown generation completed")

    def generate_index_file(self):
        """Generate main index file for the query documentation"""
        logger.info("Generating main index file")

        output_path = os.path.join(self.output_dir, 'index.md')

        # Count query patterns by category
        patterns_by_category = defaultdict(int)
        for query_data in self.queries_data.values():
            category = query_data.get('category', 'Uncategorized')
            patterns_by_category[category] += 1

        # Count tables by usage frequency
        tables_usage = defaultdict(int)
        for query_data in self.queries_data.values():
            for table in query_data.get('tables_referenced', []):
                tables_usage[table] += 1

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# SQL Query Documentation\n\n")
            f.write("This documentation catalogs and analyzes common SQL query patterns ")
            f.write(f"from a repository of {len(self.queries_data)} queries.\n\n")

            f.write("## Query Categories\n\n")
            for category, count in sorted(patterns_by_category.items(), key=lambda x: x[1], reverse=True):
                safe_cat = category.lower().replace(' ', '_')
                f.write(f"- [{category}](query_patterns/{safe_cat}.md) ({count} queries)\n")

            f.write("\n## Most Used Tables\n\n")
            f.write("| Table Name | Query Count |\n")
            f.write("|------------|------------|\n")

            # Show top 20 most used tables
            for table, count in sorted(tables_usage.items(), key=lambda x: x[1], reverse=True)[:20]:
                table_filename = table.lower().replace(' ', '_')
                f.write(f"| [{table}](tables_usage/{table_filename}.md) | {count} |\n")

        logger.info("Index file generated at %s", output_path)

    def generate_query_patterns(self):
        """Generate documentation for query patterns by category"""
        logger.info("Generating query pattern documentation")

        # Group queries by category
        queries_by_category = defaultdict(list)
        for query_id, query_data in self.queries_data.items():
            category = query_data.get('category', 'Uncategorized')
            queries_by_category[category].append((query_id, query_data))

        # Generate a page for each category
        for category, queries in queries_by_category.items():
            safe_cat = category.lower().replace(' ', '_')
            output_path = os.path.join(self.patterns_dir, f"{safe_cat}.md")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {category} Queries\n\n")
                f.write(f"This document contains {len(queries)} queries categorized as '{category}'.\n\n")

                # Complexity distribution
                complexity_counts = defaultdict(int)
                for _, query_data in queries:
                    complexity = query_data.get('complexity', 'Medium')
                    complexity_counts[complexity] += 1

                f.write("## Complexity Distribution\n\n")
                f.write("| Complexity | Count | Percentage |\n")
                f.write("|-----------|-------|------------|\n")

                total = len(queries)
                for complexity in ['Low', 'Medium', 'High', 'Very High']:
                    count = complexity_counts.get(complexity, 0)
                    percentage = (count / total) * 100 if total > 0 else 0
                    f.write(f"| {complexity} | {count} | {percentage:.1f}% |\n")

                # Table usage in this category
                tables_usage = defaultdict(int)
                for _, query_data in queries:
                    for table in query_data.get('tables_referenced', []):
                        tables_usage[table] += 1

                if tables_usage:
                    f.write("\n## Tables Used in this Category\n\n")
                    f.write("| Table Name | Query Count | Percentage |\n")
                    f.write("|------------|------------|------------|\n")

                    for table, count in sorted(tables_usage.items(), key=lambda x: x[1], reverse=True)[:15]:
                        percentage = (count / total) * 100 if total > 0 else 0
                        table_filename = table.lower().replace(' ', '_')
                        f.write(f"| [{table}](../tables_usage/{table_filename}.md) | {count} | {percentage:.1f}% |\n")

                # Sample queries
                f.write("\n## Sample Queries\n\n")

                # Limit to at most 20 examples, sorted by complexity
                for query_id, query_data in sorted(queries, key=lambda q: q[1].get('complexity', 'Medium'))[:20]:
                    sql_text = query_data.get('sql_text', '')
                    tables = ', '.join(query_data.get('tables_referenced', []))
                    complexity = query_data.get('complexity', 'Medium')
                    description = query_data.get('description', 'No description available')

                    f.write(f"### Query {query_id}\n\n")
                    f.write(f"**Complexity**: {complexity}  \n")
                    f.write(f"**Tables**: {tables}  \n")
                    f.write(f"**Description**: {description}  \n\n")
                    f.write("```sql\n")
                    f.write(sql_text)
                    f.write("\n```\n\n")

        logger.info("Generated documentation for %d query categories", len(queries_by_category))

    def generate_tables_usage_docs(self):
        """Generate documentation on how tables are used in queries"""
        logger.info("Generating tables usage documentation")

        # Group queries by table usage
        queries_by_table = defaultdict(list)
        for query_data in self.queries_data.values():
            for table in query_data.get('tables_referenced', []):
                queries_by_table[table].append(query_data)

        # Generate a page for each table with significant usage
        for table, queries in queries_by_table.items():
            if len(queries) < 2:  # Skip tables with very little usage
                continue

            table_filename = table.lower().replace(' ', '_')
            output_path = os.path.join(self.tables_dir, f"{table_filename}.md")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {table} Usage Documentation\n\n")

                # Add schema details if available
                if self.schema_data and table in self.schema_data.get('tables', {}):
                    table_schema = self.schema_data['tables'][table]
                    description = table_schema.get('description', f"Table {table}")
                    f.write(f"{description}\n\n")

                    # Link to schema documentation
                    f.write("See [full schema documentation](../../schema/tables/" + f"{table}.md) for this table.\n\n")

                f.write(f"This document describes how the `{table}` table is used across {len(queries)} queries.\n\n")

                # Usage by category
                categories = defaultdict(int)
                for query_data in queries:
                    category = query_data.get('category', 'Uncategorized')
                    categories[category] += 1

                f.write("## Usage by Category\n\n")
                f.write("| Category | Query Count | Percentage |\n")
                f.write("|----------|------------|------------|\n")

                total = len(queries)
                for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total) * 100 if total > 0 else 0
                    safe_cat = category.lower().replace(' ', '_')
                    f.write(f"| [{category}](../query_patterns/{safe_cat}.md) | {count} | {percentage:.1f}% |\n")

                # Common join patterns
                join_patterns = defaultdict(int)
                for query_data in queries:
                    for join in query_data.get('joins', []):
                        if table in join:
                            # Get the other table in the join
                            tables = join.split('_JOIN_')
                            other_table = tables[1] if tables[0] == table else tables[0]
                            join_patterns[other_table] += 1

                if join_patterns:
                    f.write("\n## Common Join Patterns\n\n")
                    f.write("| Joined With | Query Count | Percentage |\n")
                    f.write("|------------|------------|------------|\n")

                    for other_table, count in sorted(join_patterns.items(), key=lambda x: x[1], reverse=True):
                        percentage = (count / total) * 100 if total > 0 else 0
                        other_filename = other_table.lower().replace(' ', '_')
                        f.write(f"| [{other_table}](./{other_filename}.md) | {count} | {percentage:.1f}% |\n")

                # Common WHERE conditions
                where_columns = defaultdict(int)
                for query_data in queries:
                    for condition in query_data.get('where_conditions', []):
                        if condition.get('table') == table:
                            where_columns[condition.get('column', 'unknown')] += 1

                if where_columns:
                    f.write("\n## Common WHERE Conditions\n\n")
                    f.write("| Column | Query Count | Percentage |\n")
                    f.write("|--------|------------|------------|\n")

                    for column, count in sorted(where_columns.items(), key=lambda x: x[1], reverse=True)[:10]:
                        percentage = (count / total) * 100 if total > 0 else 0
                        f.write(f"| {column} | {count} | {percentage:.1f}% |\n")

                # Sample queries
                f.write("\n## Sample Queries Using This Table\n\n")

                # Limit to at most 10 examples, sorted by complexity
                for query_data in sorted(queries, key=lambda q: q.get('complexity', 'Medium'))[:10]:
                    sql_text = query_data.get('sql_text', '')
                    complexity = query_data.get('complexity', 'Medium')
                    category = query_data.get('category', 'Uncategorized')

                    f.write(f"### {category} Query (Complexity: {complexity})\n\n")
                    f.write("```sql\n")
                    f.write(sql_text)
                    f.write("\n```\n\n")

        logger.info("Generated usage documentation for %d tables", len(queries_by_table))


def generate_markdown_from_json(input_json_path, out_dir, schema_json_path=None):
    """Generate markdown documentation from query analysis JSON file

    :param input_json_path: Path to JSON query analysis file
    :param out_dir: Directory to output markdown files
    :param schema_json_path: Optional path to schema JSON for enriching documentation
    """
    try:
        # Load query data from JSON
        with open(input_json_path, 'r', encoding='utf-8') as f:
            queries_data = json.load(f)

        # Load schema data if available
        schema_data = None
        if schema_json_path:
            try:
                with open(schema_json_path, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("Failed to load schema data: %s. Continuing without schema enrichment.", e)

        # Generate markdown files
        generator = QueryMarkdownGenerator(queries_data, out_dir, schema_data)
        generator.generate_all_docs()

        logger.info("Query markdown generation completed successfully")
        return True
    except (OSError, json.JSONDecodeError) as e:
        logger.error("Error in generating markdown: %s", e)
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate markdown documentation from query analysis JSON')
    parser.add_argument('--input', '-i', required=True, help='Input JSON query analysis file path')
    parser.add_argument('--output', '-o', required=True, help='Output directory for markdown files')
    parser.add_argument('--schema', '-s', help='Optional schema JSON file to enrich documentation')

    args = parser.parse_args()

    input_path = args.input
    output_directory = args.output
    schema_path = args.schema

    if generate_markdown_from_json(input_path, output_directory, schema_path):
        print(f"Query documentation successfully generated in: {output_directory}")
    else:
        print("Query documentation generation failed. See logs for details.")
        sys.exit(1)