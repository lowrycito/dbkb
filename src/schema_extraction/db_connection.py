import os
import psycopg2
import mysql.connector
import logging
from configparser import ConfigParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_connection')

def config(filename='database.ini', section='postgresql'):
    """Read database configuration from ini file"""
    # Create a parser
    parser = ConfigParser()
    # Read config file
    parser.read(os.path.join(os.path.dirname(__file__), filename))

    # Get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')

    return db

def connect_to_db(section='postgresql'):
    """Connect to the database server (PostgreSQL or MySQL)"""
    conn = None
    try:
        # Read connection parameters
        params = config(section=section)

        if section == 'postgresql':
            # Connect to PostgreSQL
            logger.info('Connecting to the PostgreSQL database...')
            conn = psycopg2.connect(**params)

            # Create a cursor
            cur = conn.cursor()

            # Execute a statement
            logger.info('PostgreSQL database version:')
            cur.execute('SELECT version()')

        elif section == 'mysql':
            # Connect to MySQL
            logger.info('Connecting to the MySQL database...')
            conn = mysql.connector.connect(**params)

            # Create a cursor
            cur = conn.cursor()

            # Execute a statement
            logger.info('MySQL database version:')
            cur.execute('SELECT VERSION()')
        else:
            raise ValueError(f"Unsupported database type: {section}")

        # Display the database server version
        db_version = cur.fetchone()
        logger.info(db_version)

        # Close the communication with the database
        cur.close()

        return conn
    except Exception as error:
        if section == 'postgresql':
            error_type = "PostgreSQL"
        else:
            error_type = "MySQL"
        logger.error(f"{error_type} Error: {error}")
        if conn is not None:
            conn.close()
        raise

def connect_by_params(host, port, dbname, user, password, schema=None, db_type='postgresql'):
    """Connect to the database using direct parameters"""
    conn = None
    try:
        if db_type == 'postgresql':
            # Connection string
            conn_string = f"host={host} port={port} dbname={dbname} user={user} password={password}"

            # Connect to the PostgreSQL server
            logger.info(f'Connecting to PostgreSQL database {dbname} on {host}...')
            conn = psycopg2.connect(conn_string)

            # Create a cursor
            cur = conn.cursor()

            # Set search path if schema is specified
            if schema:
                cur.execute(f"SET search_path TO {schema}")
                logger.info(f"Search path set to: {schema}")

            # Execute a statement to verify connection
            cur.execute('SELECT version()')

        elif db_type == 'mysql':
            # Connect to MySQL
            logger.info(f'Connecting to MySQL database {dbname} on {host}...')
            conn = mysql.connector.connect(
                host=host,
                port=port,
                database=dbname,
                user=user,
                password=password
            )

            # Create a cursor
            cur = conn.cursor()

            # Change database if schema is specified
            if schema:
                cur.execute(f"USE {schema}")
                logger.info(f"Database changed to: {schema}")

            # Execute a statement to verify connection
            cur.execute('SELECT VERSION()')
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        # Display database version
        db_version = cur.fetchone()
        logger.info(f"Connected to: {db_version}")

        # Close the cursor but keep the connection open
        cur.close()

        return conn
    except Exception as error:
        logger.error(f"Connection error: {error}")
        if conn is not None:
            conn.close()
        raise

if __name__ == '__main__':
    # Test connection
    try:
        # Test PostgreSQL connection
        pg_conn = connect_to_db('postgresql')
        if pg_conn:
            print("PostgreSQL connection successful!")
            pg_conn.close()

        # Test MySQL connection
        mysql_conn = connect_to_db('mysql')
        if mysql_conn:
            print("MySQL connection successful!")
            mysql_conn.close()

    except Exception as e:
        print(f"Failed to connect: {e}")