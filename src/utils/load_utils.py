import csv
import re
from typing import List


def load_schema(schema_file: str) -> str:
    with open(schema_file, "r") as f:
        return f.read()


def load_query_file(path: str) -> str:
    with open(path, "r") as f:
        content = f.read()
    return re.sub(r"--.*\n", "", content)


def extract_queries(sql: str) -> List[str]:
    return [q.strip() + ";" for q in sql.split(";") if q.strip()]


def csv_to_dict_list(file_path: str) -> list[dict]:
    """
    Read a CSV file and return a list of dictionaries.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        list: List of dictionaries where each dict represents a row,
              with column headers as keys
              
    Raises:
        FileNotFoundError: If the file doesn't exist
        csv.Error: If there's an issue parsing the CSV
    """
    result = []
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            # Use DictReader to automatically create dicts with headers as keys
            reader = csv.DictReader(csvfile)
            
            # Convert each row to a dictionary and add to result list
            for row in reader:
                result.append(dict(row))
                
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    except csv.Error as e:
        raise csv.Error(f"Error parsing CSV file: {e}")
        
    return result