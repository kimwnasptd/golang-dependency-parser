import csv
import logging
import os
import shutil

log = logging.getLogger(__name__)


def initialise_folder(folder: str):
    log.info(f"Managing folder: '{folder}'")

    # Check if the folder exists
    if os.path.exists(folder):
        print(f"Folder '{folder}' found. Deleting...")
        try:
            # Delete the folder and all its contents
            shutil.rmtree(folder)
            print(f"Folder '{folder}' and its contents deleted successfully.")
        except OSError as e:
            print(f"Error: Could not delete folder '{folder}'. Reason: {e}")
            return  # Exit if deletion fails
    else:
        print(f"Folder '{folder}' does not exist. Proceeding to create it.")

    # Recreate the folder
    try:
        # os.makedirs creates all necessary intermediate directories
        os.makedirs(folder)
        print(f"Folder '{folder}' recreated successfully.")
    except OSError as e:
        print(f"Error: Could not recreate folder '{folder}'. Reason: {e}")


def read_rocks_csv(rocks_csv_path: str):
    """
    Reads a CSV file and returns its contents as a list of dictionaries.
    Each dictionary represents a row, with column headers as keys.

    Args:
        rocks_csv_path (str): The path to the CSV file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary
                    represents a row from the CSV file. Returns an empty
                    list if the file is not found or an error occurs.
    """
    data = []
    if not os.path.exists(rocks_csv_path):
        print(f"Error: CSV file not found at '{rocks_csv_path}'")
        return data

    try:
        with open(rocks_csv_path, mode="r", newline="", encoding="utf-8") as csvfile:
            # Use csv.DictReader to automatically map rows to dictionaries
            # using the header row as keys.
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        print(f"Successfully read data from '{rocks_csv_path}'.")
    except Exception as e:
        print(f"Error reading CSV file '{rocks_csv_path}': {e}")
    return data
