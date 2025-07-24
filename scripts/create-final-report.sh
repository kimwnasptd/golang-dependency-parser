#!/bin/bash

# --- Removed Setup for Demonstration Section ---

echo "Starting CSV processing from 'csv/' folder..."

# Find the first CSV file to extract the header
# This handles cases where 'csv/' might be empty or contain no CSVs
FIRST_CSV_FILE=$(ls csv/*.csv 2>/dev/null | head -n 1)

if [ -z "$FIRST_CSV_FILE" ]; then
    echo "Error: No CSV files found in the 'csv/' directory. Please ensure your CSV files are in 'csv/'."
    exit 1
fi

# Extract the header from the first CSV file
HEADER=$(head -n 1 "$FIRST_CSV_FILE")

# Use awk to process all CSV files for the initial report.csv:
# 1. Skip header lines from all input files.
# 2. Use 'Package,Version' as a unique key to identify records.
# 3. Store the full line for each unique key.
# 4. If a duplicate 'Package,Version' is found, update the 'Component' field
#    of the stored record by appending the new component (if not already present)
#    with a '+' separator.
# 5. When merging, ensure the smallest 'Layer' value is kept.
# 6. Print debug messages to stderr when components or layers are merged/updated.
# 7. Finally, print all unique/merged records to standard output.
awk -F',' '
BEGIN {
    OFS=","; # Set output field separator to comma
}

# Skip header line for all files
FNR==1 {
    next;
}

{
    # Create a unique key using Package ($1) and Version ($2)
    package_version_key = $1 "," $2;
    current_component = $4; # Get the current line''s component
    current_layer = $5;     # Get the current line''s layer

    # Check if this package_version_key has been seen before
    if (package_version_key in records) {
        # If seen, it''s a duplicate. Retrieve the existing merged line.
        split(records[package_version_key], a, ",");
        existing_component = a[4]; # Get the component field from the stored record
        existing_layer = a[5];     # Get the layer field from the stored record

        # Update component if new component is not already present
        # This regex avoids adding "comp" if "comp" or "+comp" is already present (e.g., "compA+compB" + "compB" -> no change).
        if (existing_component !~ ("(^|\\+)" current_component "(\\+|$)")) {
            a[4] = existing_component "+" current_component;
            print "DEBUG: Merging Package: " $1 ", Version: " $2 " - New Component field: " a[4] > "/dev/stderr";
        }

        # Update layer if current_layer is numerically smaller
        # Ensure comparison is numeric by coercing to number if necessary, though awk does it implicitly for <
        if (current_layer < existing_layer) {
            a[5] = current_layer;
            print "DEBUG: Updating Layer for Package: " $1 ", Version: " $2 " - New Layer: " a[5] > "/dev/stderr";
        }

        # Reconstruct the line with updated component and potentially updated layer
        records[package_version_key] = a[1] "," a[2] "," a[3] "," a[4] "," a[5];

    } else {
        # If it''s the first time seeing this package_version_key, store the entire line as is.
        records[package_version_key] = $0;
    }
}

END {
    # After processing all files, iterate through the stored records and print them.
    for (key in records) {
        print records[key];
    }
}' csv/*.csv | \
# Sort the output for report.csv:
# -t',' specifies comma as the field separator for sorting.
# -k5,5n sorts numerically based on the 5th field (Layer).
sort -t',' -k5,5n > temp_report.csv

# Combine the extracted header with the sorted data into the final report.csv
echo "$HEADER" > report.csv
cat temp_report.csv >> report.csv

echo "Initial report generated: report.csv"

echo "Generating reduced report: report-reduced.csv"

# Generate report-reduced.csv:
# This awk pass processes temp_report.csv to apply the version reduction logic.
# 1. For lines with the same package and major.minor version (e.g., v1.3.x),
#    only keep the entry with the highest patch version.
# 2. Exclude any versions that start with "v0.0.0-".
awk -F',' '
BEGIN { OFS = "," }

# Function to compare two version strings (e.g., v1.2.3 vs v1.2.10)
# Returns 1 if v1 > v2, -1 if v1 < v2, 0 if v1 == v2
# This function assumes versions are in vX.Y.Z format for comparison.
function compare_versions(v1, v2) {
    # Remove "v" prefix if present
    sub(/^v/, "", v1);
    sub(/^v/, "", v2);

    split(v1, p1, ".");
    split(v2, p2, ".");

    # Compare major, minor, patch parts numerically
    # We iterate up to 3 parts (X.Y.Z)
    for (i = 1; i <= 3; i++) {
        n1 = (p1[i] == "" ? 0 : p1[i]); # Treat missing parts as 0
        n2 = (p2[i] == "" ? 0 : p2[i]);
        if (n1 > n2) return 1;
        if (n1 < n2) return -1;
    }
    return 0; # Versions are equal
}

{
    package = $1;
    version = $2;

    # Rule 2: Don''t apply reduction for versions starting with v0.0.0-
    if (version ~ /^v0\.0\.0-/) {
        # These lines are always included as-is in the reduced report
        print $0;
        next; # Move to the next line
    }

    # Extract major.minor part (e.g., "v1.3" from "v1.3.5")
    # This regex captures "v" followed by digits and dots, up to the second dot.
    # If version is just "v1.3", it captures "v1.3". If "v1.3.5", it captures "v1.3".
    if (match(version, /^v[0-9]+\.[0-9]+/)) {
        major_minor_version_prefix = substr(version, RSTART, RLENGTH);
    } else {
        # If version format is unexpected (not vX.Y or vX.Y.Z), include as-is
        print $0;
        next;
    }

    # Create a unique key using Package and the major.minor version prefix
    key = package "," major_minor_version_prefix;

    # Check if a record for this package and major.minor version already exists
    if (key in reduced_records) {
        # Existing record found, retrieve its full line and version
        split(reduced_records[key], a, ",");
        existing_full_version = a[2];

        # Compare current version with the existing highest version
        if (compare_versions(version, existing_full_version) > 0) {
            # Current version is greater, update the record with the new line
            reduced_records[key] = $0;
            print "DEBUG: Updating reduced version for Package: " package ", Major.Minor: " major_minor_version_prefix " - New highest version: " version " (was: " existing_full_version ")" > "/dev/stderr";
        }
    } else {
        # First time seeing this package and major.minor version, store the entire line
        reduced_records[key] = $0;
    }
}

END {
    # After processing all lines, print all the reduced records
    for (k in reduced_records) {
        print reduced_records[k];
    }
}' temp_report.csv | \
# Sort the output for report-reduced.csv by Layer, just like the full report
sort -t',' -k5,5n > report-reduced.csv

# Clean up the temporary file
rm temp_report.csv

echo "CSV processing complete. Both 'report.csv' and 'report-reduced.csv' have been generated."
echo "Please check the generated CSV files for the processed data."
echo "Any merge or reduction debug logs will be printed to your terminal (stderr)."

