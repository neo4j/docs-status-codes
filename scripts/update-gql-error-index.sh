#!/bin/bash

# Script to validate and update the GQL error index
# This script follows a specific workflow to maintain error documentation consistency

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

# Step 1: Validate index.adoc against the individual files
echo "Step 1: Validating index.adoc against individual files..."
python3 "$SCRIPT_DIR/validate-error-index.py"
VALIDATION_RESULT=$?

# Step 2: Check validation result
if [ $VALIDATION_RESULT -eq 0 ]; then
    echo "✅ Validation passed! index.adoc is consistent with individual files."
    echo "No further action needed."
    exit 0
else
    echo "❌ Validation failed. Checking if there are missing entries..."

    # Step 3: Generate auto-index.adoc
    echo "Step 3: Generating auto-index.adoc from template..."
    python3 "$SCRIPT_DIR/generate-gql-error-index-from-template.py"
    GENERATION_RESULT=$?

    if [ $GENERATION_RESULT -ne 0 ] || [ ! -f "$AUTO_INDEX_FILE" ]; then
        echo "Error: Failed to generate auto-index.adoc"
        exit 1
    fi

    echo "Generation completed successfully."

    # Step 4: Validate auto-index.adoc against individual files
    echo "Step 4: Validating auto-index.adoc against individual files..."
    python3 "$SCRIPT_DIR/validate-error-auto-index.py"
    AUTO_VALIDATION_RESULT=$?

    # Step 5: If auto-index validation passes, replace index.adoc
    if [ $AUTO_VALIDATION_RESULT -eq 0 ]; then
        echo "Step 5: Auto-index validation passed! Replacing index.adoc with auto-index.adoc..."

        # Replace index with auto-index
        rm "$INDEX_FILE"
        mv "$AUTO_INDEX_FILE" "$INDEX_FILE"

        echo "✅ Update completed successfully. index.adoc has been updated."
        exit 0
    else
        echo "❌ Auto-index validation failed with exit code $AUTO_VALIDATION_RESULT."
        echo "No changes were made to index.adoc."
        echo "Please review the validation errors and fix any discrepancies."
        exit $AUTO_VALIDATION_RESULT
    fi
fi