import os
import sys
import json
import logging
import argparse
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('schema_to_markdown')

class SchemaMarkdownGenerator:
    """Generate markdown documentation from database schema JSON"""

    def __init__(self, schema_data, out_dir):
        """Initialize with schema data and output directory

        :param schema_data: Dictionary containing schema information
        :param out_dir: Directory to output markdown files
        """
        self.schema_data = schema_data
        self.output_dir = out_dir

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Create subdirectories
        self.tables_dir = os.path.join(self.output_dir, 'tables')
        os.makedirs(self.tables_dir, exist_ok=True)

        self.relationships_dir = os.path.join(self.output_dir, 'relationships')
        os.makedirs(self.relationships_dir, exist_ok=True)

        self.index_dir = os.path.join(self.output_dir, 'indexes')
        os.makedirs(self.index_dir, exist_ok=True)

    def generate_all_docs(self):
        """Generate all markdown documentation files"""
        logger.info("Starting markdown generation")

        # Generate index file
        self.generate_index_file()

        # Generate tables summary
        self.generate_tables_summary()

        # Generate individual table files
        for table_name, table_data in self.schema_data['tables'].items():
            self.generate_table_doc(table_name, table_data)

        # Generate relationship summary
        self.generate_relationships_summary()

        logger.info("Markdown generation completed")

    def generate_index_file(self):
        """Generate main index file for the documentation"""
        logger.info("Generating main index file")

        output_path = os.path.join(self.output_dir, 'index.md')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Database Schema Documentation\n\n")
            f.write("This documentation describes the database schema extracted on ")
            f.write(time.strftime('%Y-%m-%d', logging.Formatter().converter()) + "\n\n")

            f.write("## Contents\n\n")
            f.write("- [Tables Summary](tables/tables_summary.md)\n")
            f.write("- [Relationships Summary](relationships/relationships_summary.md)\n")

            f.write("\n## Tables\n\n")

            for table_name in sorted(self.schema_data['tables'].keys()):
                f.write(f"- [{table_name}](tables/{table_name}.md)\n")

        logger.info("Index file generated at %s", output_path)

    def generate_tables_summary(self):
        """Generate summary of all tables"""
        logger.info("Generating tables summary")

        output_path = os.path.join(self.tables_dir, 'tables_summary.md')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Tables Summary\n\n")
            f.write("| Table Name | Description | # Columns | Primary Key | Foreign Keys |\n")
            f.write("|------------|-------------|-----------|-------------|--------------|\n")

            for table_name, table_data in sorted(self.schema_data['tables'].items()):
                description = table_data.get('description', '').replace('|', '\\|')
                num_columns = len(table_data.get('columns', {}))
                pk = table_data.get('primary_key')
                if isinstance(pk, (list, tuple)):
                    primary_key = ', '.join(pk) if pk else 'None'
                elif pk is None:
                    primary_key = 'None'
                else:
                    primary_key = str(pk)
                foreign_keys = len(table_data.get('foreign_keys', []))

                f.write(f"| [{table_name}](./tables/{table_name}.md) | {description} | {num_columns} | {primary_key} | {foreign_keys} |\n")

        logger.info("Tables summary generated at %s", output_path)

    def generate_table_doc(self, table_name, table_data):
        """Generate documentation for a single table

        :param table_name: Name of the table
        :param table_data: Table schema data
        """
        logger.info("Generating documentation for table: %s", table_name)

        output_path = os.path.join(self.tables_dir, f"{table_name}.md")

        with open(output_path, 'w', encoding='utf-8') as f:
            # Table header
            f.write(f"# Table: {table_name}\n\n")

            # Description
            description = table_data.get('description', f"Table {table_name}")
            f.write(f"{description}\n\n")

            # Quick stats
            f.write("## Quick Statistics\n\n")
            columns_count = len(table_data.get('columns', {}))
            f.write(f"- **Columns**: {columns_count}\n")

            if table_data.get('primary_key'):
                primary_key = ', '.join(table_data['primary_key'])
                f.write(f"- **Primary Key**: {primary_key}\n")
            else:
                f.write("- **Primary Key**: None\n")

            foreign_keys_count = len(table_data.get('foreign_keys', []))
            f.write(f"- **Foreign Keys**: {foreign_keys_count}\n")

            references_count = len(table_data.get('referenced_by', []))
            f.write(f"- **Referenced By**: {references_count} tables\n")

            indexes_count = len(table_data.get('indexes', []))
            f.write(f"- **Indexes**: {indexes_count}\n\n")

            # Columns
            f.write("## Columns\n\n")
            f.write("| Column Name | Data Type | Nullable | Default | Description | PK | FK | Indexed |\n")
            f.write("|-------------|-----------|----------|---------|-------------|----|----|---------|\n")

            for col_name, col_data in sorted(table_data.get('columns', {}).items()):
                data_type = col_data.get('data_type', '').replace('|', '\\|')
                nullable = "YES" if col_data.get('is_nullable', True) else "NO"
                default = col_data.get('default')
                if default is None:
                    default = 'NULL'
                else:
                    default = str(default).replace('|', '\\|')
                desc = col_data.get('description', '').replace('|', '\\|')
                is_pk = "✓" if col_data.get('is_primary_key', False) else ""
                is_fk = "✓" if col_data.get('foreign_key') else ""
                is_indexed = "✓" if col_data.get('has_index', False) else ""

                f.write(f"| {col_name} | {data_type} | {nullable} | {default} | {desc} | {is_pk} | {is_fk} | {is_indexed} |\n")

            # Primary Key
            if table_data.get('primary_key'):
                f.write("\n## Primary Key\n\n")
                f.write("| Column |\n|--------|\n")
                for col in table_data['primary_key']:
                    f.write(f"| {col} |\n")

            # Foreign Keys
            if table_data.get('foreign_keys'):
                f.write("\n## Foreign Keys\n\n")
                f.write("| Column | Referenced Table | Referenced Column |\n")
                f.write("|--------|------------------|-------------------|\n")

                for fk in table_data.get('foreign_keys'):
                    column = fk.get('column', '')
                    ref_table = fk.get('references', {}).get('table', '')
                    ref_column = fk.get('references', {}).get('column', '')
                    f.write(f"| {column} | [{ref_table}](./{ref_table}.md) | {ref_column} |\n")

            # Referenced By
            if table_data.get('referenced_by'):
                f.write("\n## Referenced By\n\n")
                f.write("| Table | Column | Foreign Key |\n")
                f.write("|-------|--------|-------------|\n")

                for ref in table_data.get('referenced_by'):
                    ref_table = ref.get('table', '')
                    ref_column = ref.get('column', '')
                    fk_name = ref.get('via_foreign_key', '')
                    f.write(f"| [{ref_table}](./{ref_table}.md) | {ref_column} | {fk_name} |\n")

            # Indexes
            if table_data.get('indexes'):
                f.write("\n## Indexes\n\n")
                f.write("| Name | Columns | Unique | Primary |\n")
                f.write("|------|---------|--------|--------|\n")

                for idx in table_data['indexes']:
                    name = idx.get('name', '')
                    columns = ', '.join(idx.get('columns', []))
                    is_unique = "✓" if idx.get('is_unique', False) else ""
                    is_primary = "✓" if idx.get('is_primary', False) else ""
                    f.write(f"| {name} | {columns} | {is_unique} | {is_primary} |\n")

            # Sample queries (placeholder for future enhancement)
            f.write("\n## Common Join Patterns\n\n")

            # Add joins with tables referenced by foreign keys
            if table_data.get('foreign_keys'):
                for fk in table_data.get('foreign_keys'):
                    ref_table = fk.get('references', {}).get('table', '')
                    ref_column = fk.get('references', {}).get('column', '')
                    column = fk.get('column', '')

                    f.write(f"### Join with {ref_table}\n\n")
                    f.write("```sql\n")
                    f.write("SELECT t1.*, t2.*\n")
                    f.write(f"FROM {table_name} t1\n")
                    f.write(f"JOIN {ref_table} t2 ON t1.{column} = t2.{ref_column}\n")
                    f.write("```\n\n")

            # Add joins with tables referencing this table
            if table_data.get('referenced_by'):
                for ref in table_data.get('referenced_by'):
                    ref_table = ref.get('table', '')
                    ref_column = ref.get('column', '')

                    if table_data.get('primary_key'):
                        pk_column = table_data['primary_key'][0]  # Use first PK column for example

                        f.write(f"### Join with {ref_table} (referencing)\n\n")
                        f.write("```sql\n")
                        f.write("SELECT t1.*, t2.*\n")
                        f.write(f"FROM {table_name} t1\n")
                        f.write(f"JOIN {ref_table} t2 ON t1.{pk_column} = t2.{ref_column}\n")
                        f.write("```\n\n")

        logger.info("Table documentation generated at %s", output_path)

    def generate_relationships_summary(self):
        """Generate summary of database relationships"""
        logger.info("Generating relationships summary")

        output_path = os.path.join(self.relationships_dir, 'relationships_summary.md')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Database Relationships Summary\n\n")

            # Extract all relationships
            relationships = []

            for table_name, table_data in self.schema_data['tables'].items():
                for fk in table_data.get('foreign_keys', []):
                    ref_table = fk.get('references', {}).get('table', '')
                    ref_column = fk.get('references', {}).get('column', '')
                    column = fk.get('column', '')

                    relationships.append({
                        'source_table': table_name,
                        'source_column': column,
                        'target_table': ref_table,
                        'target_column': ref_column
                    })

            # Group by source table
            f.write("## Relationships by Source Table\n\n")
            f.write("| Source Table | Source Column | Target Table | Target Column |\n")
            f.write("|--------------|--------------|-------------|---------------|\n")

            for rel in sorted(relationships, key=lambda r: (r['source_table'], r['target_table'])):
                source_table = rel['source_table']
                source_column = rel['source_column']
                target_table = rel['target_table']
                target_column = rel['target_column']

                f.write(f"| [{source_table}](../tables/{source_table}.md) | {source_column} | [{target_table}](../tables/{target_table}.md) | {target_column} |\n")

            # Group by target table
            f.write("\n## Relationships by Target Table\n\n")
            f.write("| Target Table | Target Column | Source Table | Source Column |\n")
            f.write("|--------------|--------------|--------------|---------------|\n")

            for rel in sorted(relationships, key=lambda r: (r['target_table'], r['source_table'])):
                source_table = rel['source_table']
                source_column = rel['source_column']
                target_table = rel['target_table']
                target_column = rel['target_column']

                f.write(f"| [{target_table}](../tables/{target_table}.md) | {target_column} | [{source_table}](../tables/{source_table}.md) | {source_column} |\n")

        logger.info("Relationships summary generated at %s", output_path)


def generate_markdown_from_json(input_json_path, out_dir):
    """Generate markdown documentation from schema JSON file

    :param input_json_path: Path to JSON schema file
    :param out_dir: Directory to output markdown files
    """
    try:
        # Load schema data from JSON
        with open(input_json_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)

        # Generate markdown files
        generator = SchemaMarkdownGenerator(schema_data, out_dir)
        generator.generate_all_docs()

        logger.info("Markdown generation completed successfully")
        return True
    except (OSError, json.JSONDecodeError) as e:
        logger.error("Error in generating markdown: %s", e)
        return False


def generate_schema_documentation(input_json_path, out_dir):
    """Wrapper for backward compatibility with main.py imports."""
    return generate_markdown_from_json(input_json_path, out_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate markdown documentation from database schema JSON')
    parser.add_argument('--input', '-i', required=True, help='Input JSON schema file path')
    parser.add_argument('--output', '-o', required=True, help='Output directory for markdown files')

    args = parser.parse_args()

    input_path = args.input
    output_directory = args.output

    if generate_markdown_from_json(input_path, output_directory):
        print(f"Documentation successfully generated in: {output_directory}")
    else:
        print("Documentation generation failed. See logs for details.")
        sys.exit(1)