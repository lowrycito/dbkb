import os
import json
import logging
import psycopg2
import mysql.connector
from .db_connection import connect_by_params, config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('schema_extraction')

class PostgreSQLSchemaExtractor:
    """Class to extract database schema information from PostgreSQL"""

    def __init__(self, conn):
        self.conn = conn
        self.schema_data = {
            'tables': {}
        }
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs', 'schema')
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_all(self):
        """Extract all schema information"""
        logger.info("Starting PostgreSQL schema extraction process")
        self.extract_tables()
        self.extract_columns()
        self.extract_primary_keys()
        self.extract_foreign_keys()
        self.extract_indexes()
        self.save_schema_data()
        logger.info("PostgreSQL schema extraction completed successfully")
        return self.schema_data

    def extract_tables(self):
        """Extract table information"""
        logger.info("Extracting table information")

        query = """
        SELECT
            table_name,
            obj_description(pgc.oid, 'pg_class') as table_description
        FROM
            information_schema.tables t
        JOIN
            pg_class pgc ON pgc.relname = t.table_name
        JOIN
            pg_namespace nsp ON nsp.oid = pgc.relnamespace AND nsp.nspname = t.table_schema
        WHERE
            table_schema = current_schema()
            AND table_type = 'BASE TABLE'
        ORDER BY
            table_name
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                for row in rows:
                    table_name, table_description = row
                    self.schema_data['tables'][table_name] = {
                        'name': table_name,
                        'description': table_description or f"Table {table_name}",
                        'columns': {},
                        'primary_key': None,
                        'foreign_keys': [],
                        'indexes': [],
                        'referenced_by': []
                    }

                logger.info(f"Extracted information for {len(rows)} tables")
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            raise

    def extract_columns(self):
        """Extract column information"""
        logger.info("Extracting column information")

        query = """
        SELECT
            t.table_name,
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.is_nullable,
            c.column_default,
            pg_catalog.col_description(format('%s.%s',t.table_schema,t.table_name)::regclass::oid, c.ordinal_position) as column_description
        FROM
            information_schema.columns c
        JOIN
            information_schema.tables t ON c.table_name = t.table_name AND c.table_schema = t.table_schema
        WHERE
            t.table_schema = current_schema()
            AND t.table_type = 'BASE TABLE'
        ORDER BY
            t.table_name, c.ordinal_position
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                for row in rows:
                    (table_name, column_name, data_type, char_max_length,
                     numeric_precision, numeric_scale, is_nullable, column_default,
                     column_description) = row

                    # Skip tables that weren't in the previous extraction
                    if table_name not in self.schema_data['tables']:
                        continue

                    # Build full data type with precision/scale/length if applicable
                    full_data_type = data_type
                    if char_max_length:
                        full_data_type = f"{data_type}({char_max_length})"
                    elif numeric_precision and numeric_scale:
                        full_data_type = f"{data_type}({numeric_precision},{numeric_scale})"
                    elif numeric_precision:
                        full_data_type = f"{data_type}({numeric_precision})"

                    # Add column details to the schema data
                    self.schema_data['tables'][table_name]['columns'][column_name] = {
                        'name': column_name,
                        'data_type': full_data_type,
                        'is_nullable': is_nullable == 'YES',
                        'default': column_default,
                        'description': column_description or f"Column {column_name} in {table_name}",
                        'is_primary_key': False,
                        'foreign_key': None,
                        'has_index': False
                    }

                logger.info(f"Extracted information for {len(rows)} columns")
        except Exception as e:
            logger.error(f"Error extracting columns: {e}")
            raise

    def extract_primary_keys(self):
        """Extract primary key information"""
        logger.info("Extracting primary key information")

        query = """
        SELECT
            tc.table_name,
            c.column_name
        FROM
            information_schema.table_constraints tc
        JOIN
            information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        JOIN
            information_schema.columns c
            ON c.table_name = tc.table_name
            AND c.column_name = ccu.column_name
            AND c.table_schema = tc.table_schema
        WHERE
            tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = current_schema()
        ORDER BY
            tc.table_name, c.ordinal_position
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                pk_columns = {}
                for row in rows:
                    table_name, column_name = row

                    # Skip tables that weren't in the previous extraction
                    if table_name not in self.schema_data['tables']:
                        continue

                    # Group primary key columns by table
                    if table_name not in pk_columns:
                        pk_columns[table_name] = []
                    pk_columns[table_name].append(column_name)

                    # Mark column as primary key
                    if column_name in self.schema_data['tables'][table_name]['columns']:
                        self.schema_data['tables'][table_name]['columns'][column_name]['is_primary_key'] = True

                # Add primary key information to tables
                for table_name, columns in pk_columns.items():
                    self.schema_data['tables'][table_name]['primary_key'] = columns

                logger.info(f"Extracted information for primary keys in {len(pk_columns)} tables")
        except Exception as e:
            logger.error(f"Error extracting primary keys: {e}")
            raise

    def extract_foreign_keys(self):
        """Extract foreign key information"""
        logger.info("Extracting foreign key information")

        query = """
        SELECT
            tc.table_name AS table_name,
            kcu.column_name AS column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM
            information_schema.table_constraints AS tc
        JOIN
            information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN
            information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE
            tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = current_schema()
        ORDER BY
            tc.table_name, kcu.column_name
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                for row in rows:
                    table_name, column_name, foreign_table_name, foreign_column_name, constraint_name = row

                    # Skip tables that weren't in the previous extraction
                    if (table_name not in self.schema_data['tables'] or
                        foreign_table_name not in self.schema_data['tables']):
                        continue

                    # Add foreign key information to column
                    if column_name in self.schema_data['tables'][table_name]['columns']:
                        self.schema_data['tables'][table_name]['columns'][column_name]['foreign_key'] = {
                            'table': foreign_table_name,
                            'column': foreign_column_name,
                            'constraint': constraint_name
                        }

                    # Add foreign key to table's foreign keys list
                    fk = {
                        'column': column_name,
                        'references': {
                            'table': foreign_table_name,
                            'column': foreign_column_name
                        },
                        'constraint_name': constraint_name
                    }
                    self.schema_data['tables'][table_name]['foreign_keys'].append(fk)

                    # Add reference information to the referenced table
                    ref = {
                        'table': table_name,
                        'column': column_name,
                        'via_foreign_key': constraint_name
                    }
                    self.schema_data['tables'][foreign_table_name]['referenced_by'].append(ref)

                logger.info(f"Extracted information for {len(rows)} foreign key relationships")
        except Exception as e:
            logger.error(f"Error extracting foreign keys: {e}")
            raise

    def extract_indexes(self):
        """Extract index information"""
        logger.info("Extracting index information")

        query = """
        SELECT
            t.relname AS table_name,
            i.relname AS index_name,
            array_agg(a.attname) AS column_names,
            ix.indisunique AS is_unique,
            ix.indisprimary AS is_primary
        FROM
            pg_class t,
            pg_class i,
            pg_index ix,
            pg_attribute a,
            pg_namespace n
        WHERE
            t.oid = ix.indrelid
            AND i.oid = ix.indexrelid
            AND a.attrelid = t.oid
            AND a.attnum = ANY(ix.indkey)
            AND t.relkind = 'r'
            AND t.relnamespace = n.oid
            AND n.nspname = current_schema()
        GROUP BY
            t.relname, i.relname, ix.indisunique, ix.indisprimary
        ORDER BY
            t.relname, i.relname
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                for row in rows:
                    table_name, index_name, column_names, is_unique, is_primary = row

                    # Skip tables that weren't in the previous extraction
                    if table_name not in self.schema_data['tables']:
                        continue

                    # Add index information to table
                    index_info = {
                        'name': index_name,
                        'columns': column_names,
                        'is_unique': is_unique,
                        'is_primary': is_primary
                    }
                    self.schema_data['tables'][table_name]['indexes'].append(index_info)

                    # Mark columns as indexed
                    for column_name in column_names:
                        if column_name in self.schema_data['tables'][table_name]['columns']:
                            self.schema_data['tables'][table_name]['columns'][column_name]['has_index'] = True

                logger.info(f"Extracted information for {len(rows)} indexes")
        except Exception as e:
            logger.error(f"Error extracting indexes: {e}")
            raise

    def save_schema_data(self):
        """Save the schema data to JSON file"""
        output_path = os.path.join(self.output_dir, 'schema_data.json')
        with open(output_path, 'w') as f:
            json.dump(self.schema_data, f, indent=2)
        logger.info(f"Schema data saved to {output_path}")


class MySQLSchemaExtractor:
    """Class to extract database schema information from MySQL"""

    def __init__(self, conn):
        self.conn = conn
        self.schema_data = {
            'tables': {}
        }
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs', 'schema')
        os.makedirs(self.output_dir, exist_ok=True)
        self._db_name = None

        # Get the database name
        with self.conn.cursor() as cur:
            cur.execute("SELECT DATABASE()")
            self._db_name = cur.fetchone()[0]
            logger.info(f"Connected to MySQL database: {self._db_name}")

    def extract_all(self):
        """Extract all schema information"""
        logger.info("Starting MySQL schema extraction process")
        self.extract_tables()
        self.extract_columns()
        self.extract_primary_keys()
        self.extract_foreign_keys()
        self.extract_indexes()
        self.save_schema_data()
        logger.info("MySQL schema extraction completed successfully")
        return self.schema_data

    def extract_tables(self):
        """Extract table information"""
        logger.info("Extracting table information from MySQL")

        query = """
        SELECT
            TABLE_NAME,
            TABLE_COMMENT
        FROM
            information_schema.TABLES
        WHERE
            TABLE_SCHEMA = %s
            AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY
            TABLE_NAME
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (self._db_name,))
                rows = cur.fetchall()

                for row in rows:
                    table_name, table_description = row
                    self.schema_data['tables'][table_name] = {
                        'name': table_name,
                        'description': table_description or f"Table {table_name}",
                        'columns': {},
                        'primary_key': None,
                        'foreign_keys': [],
                        'indexes': [],
                        'referenced_by': []
                    }

                logger.info(f"Extracted information for {len(rows)} tables")
        except Exception as e:
            logger.error(f"Error extracting tables from MySQL: {e}")
            raise

    def extract_columns(self):
        """Extract column information"""
        logger.info("Extracting column information from MySQL")

        query = """
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            COLUMN_COMMENT
        FROM
            information_schema.COLUMNS
        WHERE
            TABLE_SCHEMA = %s
        ORDER BY
            TABLE_NAME, ORDINAL_POSITION
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (self._db_name,))
                rows = cur.fetchall()

                for row in rows:
                    (table_name, column_name, data_type, char_max_length,
                     numeric_precision, numeric_scale, is_nullable, column_default,
                     column_description) = row

                    # Skip tables that weren't in the previous extraction
                    if table_name not in self.schema_data['tables']:
                        continue

                    # Build full data type with precision/scale/length if applicable
                    full_data_type = data_type
                    if char_max_length:
                        full_data_type = f"{data_type}({char_max_length})"
                    elif numeric_precision and numeric_scale:
                        full_data_type = f"{data_type}({numeric_precision},{numeric_scale})"
                    elif numeric_precision:
                        full_data_type = f"{data_type}({numeric_precision})"

                    # Add column details to the schema data
                    self.schema_data['tables'][table_name]['columns'][column_name] = {
                        'name': column_name,
                        'data_type': full_data_type,
                        'is_nullable': is_nullable == 'YES',
                        'default': column_default,
                        'description': column_description or f"Column {column_name} in {table_name}",
                        'is_primary_key': False,
                        'foreign_key': None,
                        'has_index': False
                    }

                logger.info(f"Extracted information for {len(rows)} columns")
        except Exception as e:
            logger.error(f"Error extracting columns from MySQL: {e}")
            raise

    def extract_primary_keys(self):
        """Extract primary key information"""
        logger.info("Extracting primary key information from MySQL")

        query = """
        SELECT
            TABLE_NAME,
            COLUMN_NAME
        FROM
            information_schema.KEY_COLUMN_USAGE
        WHERE
            TABLE_SCHEMA = %s
            AND CONSTRAINT_NAME = 'PRIMARY'
        ORDER BY
            TABLE_NAME, ORDINAL_POSITION
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (self._db_name,))
                rows = cur.fetchall()

                pk_columns = {}
                for row in rows:
                    table_name, column_name = row

                    # Skip tables that weren't in the previous extraction
                    if table_name not in self.schema_data['tables']:
                        continue

                    # Group primary key columns by table
                    if table_name not in pk_columns:
                        pk_columns[table_name] = []
                    pk_columns[table_name].append(column_name)

                    # Mark column as primary key
                    if column_name in self.schema_data['tables'][table_name]['columns']:
                        self.schema_data['tables'][table_name]['columns'][column_name]['is_primary_key'] = True

                # Add primary key information to tables
                for table_name, columns in pk_columns.items():
                    self.schema_data['tables'][table_name]['primary_key'] = columns

                logger.info(f"Extracted information for primary keys in {len(pk_columns)} tables")
        except Exception as e:
            logger.error(f"Error extracting primary keys from MySQL: {e}")
            raise

    def extract_foreign_keys(self):
        """Extract foreign key information"""
        logger.info("Extracting foreign key information from MySQL")

        query = """
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME,
            CONSTRAINT_NAME
        FROM
            information_schema.KEY_COLUMN_USAGE
        WHERE
            TABLE_SCHEMA = %s
            AND REFERENCED_TABLE_SCHEMA IS NOT NULL
        ORDER BY
            TABLE_NAME, COLUMN_NAME
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (self._db_name,))
                rows = cur.fetchall()

                for row in rows:
                    table_name, column_name, foreign_table_name, foreign_column_name, constraint_name = row

                    # Skip tables that weren't in the previous extraction
                    if (table_name not in self.schema_data['tables'] or
                        foreign_table_name not in self.schema_data['tables']):
                        continue

                    # Add foreign key information to column
                    if column_name in self.schema_data['tables'][table_name]['columns']:
                        self.schema_data['tables'][table_name]['columns'][column_name]['foreign_key'] = {
                            'table': foreign_table_name,
                            'column': foreign_column_name,
                            'constraint': constraint_name
                        }

                    # Add foreign key to table's foreign keys list
                    fk = {
                        'column': column_name,
                        'references': {
                            'table': foreign_table_name,
                            'column': foreign_column_name
                        },
                        'constraint_name': constraint_name
                    }
                    self.schema_data['tables'][table_name]['foreign_keys'].append(fk)

                    # Add reference information to the referenced table
                    ref = {
                        'table': table_name,
                        'column': column_name,
                        'via_foreign_key': constraint_name
                    }
                    self.schema_data['tables'][foreign_table_name]['referenced_by'].append(ref)

                logger.info(f"Extracted information for {len(rows)} foreign key relationships")
        except Exception as e:
            logger.error(f"Error extracting foreign keys from MySQL: {e}")
            raise

    def extract_indexes(self):
        """Extract index information"""
        logger.info("Extracting index information from MySQL")

        query = """
        SELECT
            TABLE_NAME,
            INDEX_NAME,
            GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS column_names,
            NON_UNIQUE = 0 AS is_unique,
            INDEX_NAME = 'PRIMARY' AS is_primary
        FROM
            information_schema.STATISTICS
        WHERE
            TABLE_SCHEMA = %s
        GROUP BY
            TABLE_NAME, INDEX_NAME, NON_UNIQUE
        ORDER BY
            TABLE_NAME, INDEX_NAME
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (self._db_name,))
                rows = cur.fetchall()

                for row in rows:
                    table_name, index_name, column_names_str, is_unique, is_primary = row

                    # Skip tables that weren't in the previous extraction
                    if table_name not in self.schema_data['tables']:
                        continue

                    # Convert comma-separated column names to a list
                    column_names = column_names_str.split(',')

                    # Add index information to table
                    index_info = {
                        'name': index_name,
                        'columns': column_names,
                        'is_unique': is_unique,
                        'is_primary': is_primary
                    }
                    self.schema_data['tables'][table_name]['indexes'].append(index_info)

                    # Mark columns as indexed
                    for column_name in column_names:
                        if column_name in self.schema_data['tables'][table_name]['columns']:
                            self.schema_data['tables'][table_name]['columns'][column_name]['has_index'] = True

                logger.info(f"Extracted information for {len(rows)} indexes")
        except Exception as e:
            logger.error(f"Error extracting indexes from MySQL: {e}")
            raise

    def save_schema_data(self):
        """Save the schema data to JSON file"""
        output_path = os.path.join(self.output_dir, 'schema_data.json')
        with open(output_path, 'w') as f:
            json.dump(self.schema_data, f, indent=2)
        logger.info(f"Schema data saved to {output_path}")


def extract_schema_to_json(host, port, dbname, user, password, schema, db_type='postgresql'):
    """Main function to extract schema and save it to JSON"""
    try:
        # Connect to the database
        conn = connect_by_params(host, port, dbname, user, password, schema, db_type)

        # Create extractor based on database type
        if db_type == 'postgresql':
            extractor = PostgreSQLSchemaExtractor(conn)
        elif db_type == 'mysql':
            extractor = MySQLSchemaExtractor(conn)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        # Run extraction
        schema_data = extractor.extract_all()

        # Close connection
        conn.close()

        return schema_data
    except Exception as e:
        logger.error(f"Error in schema extraction: {e}")
        raise


if __name__ == '__main__':
    try:
        # Read config from file - using mysql section (can be overridden via command line)
        params = config(section='mysql')

        # Extract schema
        schema_data = extract_schema_to_json(
            params['host'],
            params['port'],
            params['database'],
            params['user'],
            params['password'],
            params.get('schema'),
            'mysql'  # Use MySQL as the default
        )

        # Print summary
        print(f"Extracted schema information for {len(schema_data['tables'])} tables")

    except Exception as e:
        logger.error(f"Schema extraction failed: {e}")
        print(f"Error: {e}")