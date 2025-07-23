#!/usr/bin/env python3

import os
import json
import re
import hashlib
from pathlib import Path
from collections import defaultdict

def extract_embedding_query(content):
    """Extract the Embedding-Ready Query section from markdown content."""
    pattern = r'## Embedding-Ready Query\s*```sql\s*(.*?)```'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def extract_database_from_filename(filename):
    """Extract database identifier from filename (epic prefix)."""
    # Extract epic number from filename like "epic10000000_query_0001.md"
    match = re.match(r'epic(\w+)_query_', filename)
    if match:
        return f"epic{match.group(1)}"
    return "unknown"

def hash_query(sql_query):
    """Create a hash of the SQL query for deduplication."""
    if not sql_query:
        return None

    # Normalize the query for consistent hashing
    normalized = re.sub(r'\s+', ' ', sql_query.strip().lower())
    return hashlib.md5(normalized.encode()).hexdigest()

def identify_main_table(sql_query):
    """Identify the main table from the SQL query."""
    if not sql_query:
        return None

    from_pattern = r'FROM\s+(\w+)'
    match = re.search(from_pattern, sql_query, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def extract_all_tables(sql_query):
    """Extract all table names from the SQL query."""
    if not sql_query:
        return []

    tables = []

    # Find FROM clause tables
    from_pattern = r'FROM\s+(\w+)'
    from_match = re.search(from_pattern, sql_query, re.IGNORECASE)
    if from_match:
        tables.append(from_match.group(1))

    # Find JOIN clause tables
    join_pattern = r'JOIN\s+(\w+)'
    join_matches = re.findall(join_pattern, sql_query, re.IGNORECASE)
    tables.extend(join_matches)

    # Remove duplicates while preserving order
    return list(dict.fromkeys(tables))

def main():
    queries_dir = "/Volumes/Code/dbkb/docs/queries"

    print("Starting extraction with deduplication...")
    print(f"Queries directory: {queries_dir}")

    if not os.path.exists(queries_dir):
        print(f"Error: Directory does not exist")
        return

    queries_path = Path(queries_dir)
    md_files = list(queries_path.glob("*.md"))

    print(f"Found {len(md_files)} markdown files")

    # Use dictionary to track unique queries by hash
    unique_queries = {}
    database_tracking = defaultdict(set)  # hash -> set of databases

    total_files = len(md_files)
    processed_files = 0
    files_with_queries = 0
    duplicate_count = 0

    for i, file_path in enumerate(md_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            processed_files += 1
            database = extract_database_from_filename(file_path.name)

            embedding_query = extract_embedding_query(content)

            if embedding_query:
                files_with_queries += 1

                # Create hash for deduplication
                query_hash = hash_query(embedding_query)

                if query_hash:
                    # Track which databases contain this query
                    database_tracking[query_hash].add(database)

                    if query_hash not in unique_queries:
                        # First time seeing this query
                        main_table = identify_main_table(embedding_query)
                        all_tables = extract_all_tables(embedding_query)

                        unique_queries[query_hash] = {
                            "query_hash": query_hash,
                            "main_table": main_table,
                            "all_tables": all_tables,
                            "embedding_ready_query": embedding_query,
                            "databases": []  # Will be populated later
                        }
                    else:
                        duplicate_count += 1

                if files_with_queries % 100 == 0:
                    print(f"Found {files_with_queries} queries so far ({duplicate_count} duplicates)...")

            if (i + 1) % 1000 == 0:
                print(f"Processed {i + 1} files")

        except Exception as e:
            print(f"Error with {file_path.name}: {e}")

    # Update queries with database information
    for query_hash, query_info in unique_queries.items():
        query_info["databases"] = sorted(list(database_tracking[query_hash]))

    print(f"\nProcessing complete!")
    print(f"Total files: {total_files}")
    print(f"Processed files: {processed_files}")
    print(f"Files with queries: {files_with_queries}")
    print(f"Unique queries: {len(unique_queries)}")
    print(f"Duplicate queries removed: {duplicate_count}")

    # Create database summary
    database_counts = defaultdict(int)
    for databases in database_tracking.values():
        for db in databases:
            database_counts[db] += 1

    # Create table summary
    table_counts = {}
    for query in unique_queries.values():
        main_table = query.get("main_table")
        if main_table:
            table_counts[main_table] = table_counts.get(main_table, 0) + 1

    # Sort by count
    sorted_tables = sorted(table_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_databases = sorted(database_counts.items(), key=lambda x: x[1], reverse=True)

    # Create final catalog structure
    catalog = {
        "metadata": {
            "total_files": total_files,
            "processed_files": processed_files,
            "files_with_queries": files_with_queries,
            "unique_queries": len(unique_queries),
            "duplicate_queries_removed": duplicate_count,
            "extraction_date": "2025-05-23"
        },
        "queries": list(unique_queries.values()),
        "table_summary": dict(sorted_tables),
        "database_summary": dict(sorted_databases)
    }

    # Save catalog
    output_file = "/Volumes/Code/dbkb/query_catalog_deduplicated.json"
    with open(output_file, 'w') as f:
        json.dump(catalog, f, indent=2)

    print(f"\nCatalog saved to: {output_file}")

    print(f"\nTop 10 tables by query count:")
    for i, (table, count) in enumerate(sorted_tables[:10]):
        print(f"{i+1:2d}. {table}: {count} queries")

    print(f"\nTop 10 databases by query count:")
    for i, (database, count) in enumerate(sorted_databases[:10]):
        print(f"{i+1:2d}. {database}: {count} queries")

    # Show some stats about cross-database queries
    cross_db_queries = [q for q in unique_queries.values() if len(q["databases"]) > 1]
    print(f"\nQueries found in multiple databases: {len(cross_db_queries)}")

    if cross_db_queries:
        print("Sample cross-database queries:")
        for i, query in enumerate(cross_db_queries[:5]):
            print(f"  {i+1}. Hash: {query['query_hash'][:8]}... - Databases: {', '.join(query['databases'])}")

if __name__ == "__main__":
    main()
