#!/bin/bash

# Script to generate, validate, and update the GQL error index
# This script will:
# 1. Generate auto-index.adoc using the template
# 2. Validate that it matches the content of index.adoc
# 3. If validation passes, replace index.adoc with auto-index.adoc

set -e  # Exit on any error

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ERRORS_DIR="$PROJECT_ROOT/modules/ROOT/pages/errors/gql-errors"
INDEX_FILE="$ERRORS_DIR/index.adoc"
AUTO_INDEX_FILE="$ERRORS_DIR/auto-index.adoc"

# Check if files exist
if [ ! -f "$INDEX_FILE" ]; then
    echo "Error: index.adoc not found at $INDEX_FILE"
    exit 1
fi

echo "===== Starting GQL Error Index Update Process ====="

# Step 1: Generate auto-index.adoc
echo "Generating auto-index.adoc from template..."
python3 "$SCRIPT_DIR/generate-gql-error-index-from-template.py"

if [ ! -f "$AUTO_INDEX_FILE" ]; then
    echo "Error: Failed to generate auto-index.adoc"
    exit 1
fi

echo "Generation completed successfully."

# Step 2: Validate auto-index.adoc against the files.
echo "Validating auto-index.adoc against the files and index.adoc..."
python3 "$SCRIPT_DIR/validate_error_index.py"
VALIDATION_RESULT=$?

# Step 3: If validation passes, replace index.adoc with auto-index.adoc
if [ $VALIDATION_RESULT -eq 0 ]; then
    echo "Validation passed! Replacing index.adoc with auto-index.adoc..."

    # Replace index with auto-index
    rm "$INDEX_FILE"
    mv "$AUTO_INDEX_FILE" "$INDEX_FILE"

    echo "✅ Update completed successfully. index.adoc has been updated."
else
    echo "❌ Validation failed with exit code $VALIDATION_RESULT. No changes were made to index.adoc."
    echo "Please review the validation errors and fix any discrepancies."
fi

exit $VALIDATION_RESULT