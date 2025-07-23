import csv
import os
from parser.package import PackageLayer
from typing import List


def create_report(name: str, layers: List[PackageLayer]):
    """Create a CSV report based on the layers"""
    report_path = os.path.basename(name) + "-sd-report.csv"
    headers = ["Package", "Version", "Bootstrap", "Layer"]

    data = []
    for i, layer in enumerate(layers):
        for package in layer.packages:
            bootstrap = ""
            if layer.bootstrap:
                bootstrap = "Bootstrap"

            data.append([package.import_name, package.version, bootstrap, i])
    try:
        # Open the file in write mode ('w') with newline='' to prevent extra blank rows
        with open(report_path, "w", newline="", encoding="utf-8") as csvfile:
            # Create a CSV writer object
            csv_writer = csv.writer(csvfile)

            # Write the header row
            csv_writer.writerow(headers)

            # Write the data rows
            csv_writer.writerows(data)

        print(f"CSV file '{report_path}' created successfully with data.")

    except IOError as e:
        print(f"Error writing to file '{report_path}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
