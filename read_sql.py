import csv
import os
import re

from src.config import logger
from src.utils.load_utils import extract_queries, load_query_file


def clean_sql_query(sql_content):
    """
    Clean the SQL query by removing comments and converting to a single line string.
    """
    # Remove single-line comments (-- comments)
    lines = sql_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove comments but keep the rest of the line
        if '--' in line:
            line = line[:line.index('--')]
        
        # Skip empty lines and lines with only whitespace
        if line.strip():
            cleaned_lines.append(line.strip())
    
    # Join all lines into a single string with spaces
    cleaned_sql = ' '.join(cleaned_lines)
    
    # Normalize whitespace - replace multiple spaces with single space
    cleaned_sql = re.sub(r'\s+', ' ', cleaned_sql)
    cleaned_sql = cleaned_sql.strip()
    
    return cleaned_sql

def sql_data_to_csv(sql_csv_data, output_csv_file):
    """
    Write SQL data to a CSV file.

    Args:
        sql_csv_data (list): List of SQL data rows to write
        output_csv_file (str): Path to the output CSV file
    """
    # Write to CSV
    try:
        with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header 
            writer.writerow(['', 'db_id', 'original_sql'])
            
            # Write data
            writer.writerows(sql_csv_data)

        print(f"\nSuccessfully created '{output_csv_file}' with {len(sql_csv_data)} queries")

    except Exception as e:
        print(f"Error writing CSV file: {e}")

def main():
    """
    Main function to run the script with command line arguments.
    Usage: python read_sql.py <db_id> <input_directory> <output_csv_file>
    """
    import argparse

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Aggregate SQL files into a CSV format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            python read_sql.py tpch ./sql_files queries.csv
            python read_sql.py dsb /path/to/queries output.csv
        """
    )
    
    parser.add_argument('db_id', 
                       help='Database identifier (e.g., tpch, sakila, etc.)')
    parser.add_argument('input_directory', 
                       help='Directory containing .sql files')
    parser.add_argument('output_csv_file', 
                       help='Output CSV file path')
    
    # Parse arguments
    try:
        args = parser.parse_args()
    except SystemExit:
        return
    
    db_id = args.db_id
    input_directory = args.input_directory
    output_csv_file = args.output_csv_file
    
    print(f"Database ID: {db_id}")
    print(f"Input directory: {input_directory}")
    print(f"Output CSV file: {output_csv_file}")
    print("-" * 50)

    queries_dir = os.path.join(input_directory)
    templates = [t for t in os.listdir(queries_dir) if os.path.isdir(os.path.join(queries_dir, t))]
    logger.info(f"Available query templates: {templates}")

    sql_csv_data = []
    sql_idx = 1
    for template in templates:
        logger.info(f"Processing template: {template}")
        files_count_in_template_dir = len([f for f in os.listdir(os.path.join(queries_dir, template)) if f.endswith('.sql')])
        for idx in range(files_count_in_template_dir):
            file_path = os.path.join(queries_dir, template, f"{template}_{idx}.sql")
            if not os.path.exists(file_path):
                continue

            logger.info(f"Processing query {idx} for template {template}")

            sql_content = load_query_file(file_path)
            queries = extract_queries(sql_content)
            clean_queries = [clean_sql_query(query) for query in queries]

            print(clean_queries[0])  # Print the first cleaned query for verification

            for _, query in enumerate(clean_queries):
                sql_csv_data.append([sql_idx, db_id, query])
                sql_idx += 1

    try:
        sql_data_to_csv(sql_csv_data, output_csv_file)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()