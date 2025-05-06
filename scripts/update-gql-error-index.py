#!/usr/bin/env python3

import os
import subprocess
import shutil

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
errors_dir = os.path.join(project_root, "modules", "ROOT", "pages", "errors", "gql-errors")
index_file = os.path.join(errors_dir, "index.adoc")
auto_index_file = os.path.join(errors_dir, "auto-index.adoc")

def run_python_script(script_name):
    """Run a Python script and return its exit code"""
    script_path = os.path.join(script_dir, script_name)
    result = subprocess.run(["python3", script_path], capture_output=True, text=True)
    print(result.stdout)
    return result.returncode

# Main workflow
def main():
    print("===== Starting GQL Error Index Update Process =====")

    # Step 1: Validate index.adoc
    print("Step 1: Validating index.adoc against individual files...")
    validation_result = run_python_script("validate-error-index.py")

    # Step 2: Check validation result
    if validation_result == 0:
        print("✅ Validation passed! No further action needed.")
        return 0

    # Step 3: Generate auto-index.adoc
    print("Step 3: Generating auto-index.adoc from template...")
    generation_result = run_python_script("generate-gql-error-index-from-template.py")

    if generation_result != 0 or not os.path.exists(auto_index_file):
        print("Error: Failed to generate auto-index.adoc")
        return 1

    # Step 4: Validate auto-index.adoc
    print("Step 4: Validating auto-index.adoc against individual files...")
    auto_validation_result = run_python_script("validate-error-auto-index.py")

    # Step 5: If auto-index validation passes, replace index.adoc
    if auto_validation_result == 0:
        print("Step 5: Auto-index validation passed! Replacing index.adoc...")

        # Replace index with auto-index
        os.remove(index_file)
        os.rename(auto_index_file, index_file)

        print("✅ Update completed successfully.")
        return 0
    else:
        print("❌ Auto-index validation failed.")
        print("No changes were made to index.adoc.")
        return auto_validation_result

if __name__ == "__main__":
    exit(main())