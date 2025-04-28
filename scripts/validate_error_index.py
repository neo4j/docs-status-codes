#!/usr/bin/env python3

import os
import re
from pathlib import Path

def get_error_codes_from_files(errors_dir):
    """Get all error codes from individual .adoc files."""
    error_codes = set()
    
    # Get all .adoc files that have 5-character names (error codes)
    for file in os.listdir(errors_dir):
        if file.endswith('.adoc') and len(file) == 10 and file != 'index.adoc' and file != 'auto-index.adoc':
            error_codes.add(file[:-5])  # Remove .adoc extension
            
    return error_codes

def get_error_codes_from_index(index_file):
    """Extract error codes from the index file."""
    error_codes = set()
    
    with open(index_file, 'r') as f:
        content = f.read()
        
    # Find all xref patterns that match our error code format
    # Pattern looks for: xref:errors/gql-errors/XXXXX.adoc[XXXXX]
    pattern = r'xref:errors/gql-errors/([A-Z0-9]{5})\.adoc\[\1\]'
    matches = re.findall(pattern, content)
    
    error_codes.update(matches)
    return error_codes

def validate_index(errors_dir, index_file):
    """Compare error codes between individual files and index."""
    # Get error codes from both sources
    file_codes = get_error_codes_from_files(errors_dir)
    index_codes = get_error_codes_from_index(index_file)
    
    # Find missing and extra codes
    missing_in_index = file_codes - index_codes
    extra_in_index = index_codes - file_codes
    
    # Print results
    print(f"Total error codes in files: {len(file_codes)}")
    print(f"Total error codes in index: {len(index_codes)}")
    print()
    
    if missing_in_index:
        print("Error codes present in files but missing from index:")
        for code in sorted(missing_in_index):
            print(f"  - {code}")
    else:
        print("No error codes are missing from the index.")
    
    if extra_in_index:
        print("\nError codes present in index but missing as files:")
        for code in sorted(extra_in_index):
            print(f"  - {code}")
    else:
        print("\nNo extra error codes in the index.")
    
    # Return True if everything matches
    return len(missing_in_index) == 0 and len(extra_in_index) == 0

def main():
    # Get the script's directory
    script_dir = Path(__file__).parent.absolute()
    
    # Navigate to the gql-errors directory
    errors_dir = script_dir.parent / 'modules' / 'ROOT' / 'pages' / 'errors' / 'gql-errors'
    auto_index_file = errors_dir / 'auto-index.adoc'
    
    print("Validating auto-index.adoc against individual error files...\n")
    
    if not auto_index_file.exists():
        print("Error: auto-index.adoc not found! Please run generate_gql_error_index.py first.")
        return
    
    success = validate_index(errors_dir, auto_index_file)
    
    if success:
        print("\nValidation successful! All error codes match between files and index.")
    else:
        print("\nValidation failed! Please check the discrepancies listed above.")

if __name__ == '__main__':
    main()
