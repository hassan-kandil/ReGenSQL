import json

from src.config import logger

def read_json(file_path: str) -> dict:
    """
    Read a JSON file and return the data as a dictionary

    Args:
        file_path (str): Path to the JSON file

    Returns:
        dict: The JSON data
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        logger.info(f"Successfully read {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"Error: File {file_path} not found.")
        raise 
    except json.JSONDecodeError as e:
        logger.error(f"Error: Invalid JSON format in {file_path}. {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise

def write_json(data: dict, file_path: str, indent: int = 4):
    """
    Write a dictionary to a JSON file

    Args:
        data (dict): The data to write
        file_path (str): Path where to save the JSON file
        indent (int): Number of spaces for indentation (default: 4)

    Returns:
        None
    """
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=indent)
        logger.info(f"Successfully wrote to {file_path}")
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        raise
