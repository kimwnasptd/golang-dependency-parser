#!/bin/bash

# --- Configuration ---
CSV_FILE="$1" # The CSV file is expected as the first argument
REPOS_DIR="repos" # Directory where repositories will be cloned

# Uncomment the line below for verbose debugging output
# set -x

# --- Error Handling ---
# Exit immediately if a command exits with a non-zero status.
set -euo pipefail

# Function to display usage information
usage() {
  echo "Usage: $0 <path_to_csv_file>"
  echo "Example: $0 input.csv"
  echo ""
  echo "The CSV file must have the following header and structure:"
  echo "Rock,Language,Repo,Commit/Tag,go.mod dir,pyproject.toml dir,requirements.txt dir"
  echo "charmedkubeflow/dex:2.41.1-1d3fe19,Go,https://github.com/dexidp/dex,knative-v1.16.0,,,"
  exit 1
}

# Check if a CSV file path is provided
if [ -z "$CSV_FILE" ]; then
  echo "Error: No CSV file specified."
  usage
fi

# Check if the CSV file exists
if [ ! -f "$CSV_FILE" ]; then
  echo "Error: CSV file '$CSV_FILE' not found."
  exit 1
fi

# --- Pre-checks ---
# Check if poetry command is available
if ! command -v poetry &> /dev/null
then
    echo "Error: 'poetry' command not found. Please ensure Poetry is installed and in your system's PATH."
    exit 1
fi

# --- Directory Management ---
echo "--- Cleaning up and setting up '$REPOS_DIR' directory ---"
if [ -d "$REPOS_DIR" ]; then
  echo "Deleting existing '$REPOS_DIR'..."
  rm -rf "$REPOS_DIR"
fi
echo "Creating '$REPOS_DIR'..."
mkdir -p "$REPOS_DIR"
echo "Directory setup complete."

# --- Process CSV Entries ---
echo "--- Processing CSV file: '$CSV_FILE' ---"

# Read the CSV file line by line, skipping the header (tail -n +2)
# IFS=',' sets the Internal Field Separator to comma for CSV parsing
# -r prevents backslash escapes from being interpreted
tail -n +2 "$CSV_FILE" | while IFS=',' read -r Rock Language Repo CommitTag GoModDir PyProjectTomlDir RequirementsTxtDir; do
  # Trim whitespace from variables (important for paths and URLs)
  Rock=$(echo "$Rock" | xargs)
  Language=$(echo "$Language" | xargs)
  Repo=$(echo "$Repo" | xargs)
  CommitTag=$(echo "$CommitTag" | xargs)
  GoModDir=$(echo "$GoModDir" | xargs)
  PyProjectTomlDir=$(echo "$PyProjectTomlDir" | xargs)
  RequirementsTxtDir=$(echo "$RequirementsTxtDir" | xargs)

  echo ""
  echo "--- Processing entry: $Rock ---"
  echo "  Repo: $Repo"
  echo "  Commit/Tag: $CommitTag"
  echo "  Go.mod Dir: '$GoModDir'"

  # Extract repository name from the URL
  # Example: https://github.com/dexidp/dex -> dex
  REPO_NAME=$(basename "$Repo" .git)
  REPO_PATH="$REPOS_DIR/$REPO_NAME" # Full path to the cloned repository

  # a. Clone the GH repo, or use an existing local repo
  if [ -d "$REPO_PATH" ]; then
    echo "  Repository '$REPO_NAME' already exists locally. Using existing."
    (cd "$REPO_PATH" && git pull) || { echo "  Warning: Failed to pull latest changes for $REPO_NAME. Continuing anyway."; }
  else
    echo "  Cloning repository '$Repo' into '$REPO_PATH'..."
    git clone "$Repo" "$REPO_PATH" || { echo "Error: Failed to clone $Repo. Skipping this entry."; continue; }
  fi

  # c. git checkout to the commit/tag (this still needs to happen inside the repo)
  (
    cd "$REPO_PATH" || { echo "Error: Failed to change directory to $REPO_PATH for checkout. Skipping this entry."; continue; }
    echo "  Checking out '$CommitTag'..."
    git checkout "$CommitTag" || { echo "Error: Failed to checkout '$CommitTag' for '$REPO_NAME'. Continuing with next entry."; return 1; } # Use return 1 to exit subshell
  ) # End of subshell for git checkout
  if [ $? -ne 0 ]; then
    echo "  An error occurred during git checkout for '$REPO_NAME'. Moving to next entry."
    continue # Skip to the next CSV entry
  fi

  # d. Run poetry run parse. This command will now be run from the script's original directory.
  # Determine the subdirectory within the cloned repo for 'go.mod dir'.
  # If GoModDir is empty, use an empty string, which will result in just 'scripts/'
  # being appended to the repo path.
  TARGET_SUB_DIR=""
  if [ -n "$GoModDir" ]; then
    TARGET_SUB_DIR="$GoModDir"
    echo "  'go.mod dir' specified. Using subdirectory: '$TARGET_SUB_DIR'."
  else
    TARGET_SUB_DIR="" # Empty string means the repo root itself for path construction
    echo "  'go.mod dir' not specified. Defaulting to repository root for 'parse' target."
  fi

  # Construct the full path to be passed to poetry run parse.
  # This path is relative to the script's execution directory.
  # It combines the REPOS_DIR, REPO_NAME, "scripts" prefix, and the target subdirectory.
  # Example: repos/dex/scripts/some/path or repos/dex/scripts/
  POETRY_PARSE_PATH="$REPO_PATH/$TARGET_SUB_DIR"

  echo "  Running 'poetry run parse $POETRY_PARSE_PATH' from script's directory..."
  # Ensure poetry is available and the parse command works in your environment
  poetry run parse "$POETRY_PARSE_PATH" || { echo "Warning: 'poetry run parse $POETRY_PARSE_PATH' failed for '$REPO_NAME'. Continuing."; }

done

echo ""
echo "--- Script execution complete ---"

