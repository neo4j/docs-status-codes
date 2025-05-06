#!/usr/bin/env python3

import os
import re
from pathlib import Path
import argparse
import sys
from difflib import ndiff

def get_error_codes_from_index(index_file):
    """Extract error codes and their descriptions from the index file."""
    error_codes = {}

    try:
        with open(index_file, 'r') as f:
            content = f.read()

        # Find all error code entries with descriptions
        pattern = r'=== xref:errors/gql-errors/([A-Z0-9]{5})\.adoc\[\1\]\s*\n\s*\n\s*Status description:: (.*?)(?=\n\s*\n|\n===|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)

        for code, desc in matches:
            error_codes[code] = desc.strip()

        return error_codes
    except Exception as e:
        print(f"Error reading index file {index_file}: {e}")
        return {}

def get_page_roles_from_index(index_file):
    """Extract page roles for error codes from the index file."""
    roles = {}

    try:
        with open(index_file, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            role_match = re.search(r'\[role=label--([^\]]+)\]', line)
            if role_match and i + 1 < len(lines):
                code_match = re.search(r'xref:errors/gql-errors/([A-Z0-9]{5})\.adoc', lines[i+1])
                if code_match:
                    roles[code_match.group(1)] = role_match.group(1)

        return roles
    except Exception as e:
        print(f"Error reading index file for roles {index_file}: {e}")
        return {}

def get_error_codes_from_files(errors_dir):
    """Get error codes and descriptions from individual error files."""
    error_codes = {}

    try:
        for file in os.listdir(errors_dir):
            if file.endswith('.adoc') and file != 'index.adoc' and file != 'auto-index.adoc':
                error_code = file[:-5]  # Remove .adoc extension
                file_path = os.path.join(errors_dir, file)

                # Extract description from file
                description = extract_description_from_file(file_path)

                if description:
                    error_codes[error_code] = description
                else:
                    error_codes[error_code] = None

        return error_codes
    except Exception as e:
        print(f"Error scanning error files directory {errors_dir}: {e}")
        return {}

def extract_description_from_file(file_path):
    """Extract the status description from an error file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Try different patterns to match the description
        patterns = [
            r'== Status description\s*\n(.*?)(?=\n\n|\n==|\Z)',  # Format with standalone line
            r'Status description::\s*(.*?)(?=\n\n|\n==|\Z)'      # Format with Status description:: prefix
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                description = match.group(1).strip()
                if description.startswith('Status description::'):
                    description = description[len('Status description::'):].strip()
                return description

        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def get_page_roles_from_files(errors_dir):
    """Get page roles from individual error files."""
    roles = {}

    try:
        for file in os.listdir(errors_dir):
            if file.endswith('.adoc') and file != 'index.adoc' and file != 'auto-index.adoc':
                error_code = file[:-5]  # Remove .adoc extension
                file_path = os.path.join(errors_dir, file)

                # Extract page role from file
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith(':page-role:'):
                            roles[error_code] = line.strip()[11:].strip()
                            break

        return roles
    except Exception as e:
        print(f"Error scanning error files for roles {errors_dir}: {e}")
        return {}

def format_description(desc, max_len=60):
    """Format a description for display, truncating if necessary."""
    if not desc:
        return "MISSING"
    if len(desc) > max_len:
        return f"{desc[:max_len]}..."
    return desc

def validate_error_parity(errors_dir, auto_index_file, verbose=False):
    """Validate error code parity between auto-index and individual files."""
    # Get error codes from auto-index and files
    auto_index_codes = get_error_codes_from_index(auto_index_file)
    file_codes = get_error_codes_from_files(errors_dir)

    # Get page roles
    auto_index_roles = get_page_roles_from_index(auto_index_file)
    file_roles = get_page_roles_from_files(errors_dir)

    # Find missing files and entries
    codes_in_auto_index_not_in_files = set(auto_index_codes.keys()) - set(file_codes.keys())
    codes_in_files_not_in_auto_index = set(file_codes.keys()) - set(auto_index_codes.keys())

    # Find description mismatches
    description_mismatches = []
    for code in set(auto_index_codes.keys()) & set(file_codes.keys()):
        auto_index_desc = auto_index_codes[code] if code in auto_index_codes else None
        file_desc = file_codes[code] if code in file_codes else None

        # If file has no description, this isn't a mismatch, just incomplete documentation
        if file_desc is None:
            continue

        # Compare normalized descriptions (strip whitespace and standardize spacing)
        if auto_index_desc and file_desc:
            auto_index_desc_norm = re.sub(r'\s+', ' ', auto_index_desc.strip())
            file_desc_norm = re.sub(r'\s+', ' ', file_desc.strip())

            if auto_index_desc_norm != file_desc_norm:
                description_mismatches.append((code, auto_index_desc, file_desc))

    # Find role mismatches
    role_mismatches = []
    for code in set(auto_index_roles.keys()) | set(file_roles.keys()):
        auto_index_role = auto_index_roles.get(code)
        file_role = file_roles.get(code)

        if auto_index_role != file_role:
            role_mismatches.append((code, auto_index_role, file_role))

    # Print results
    print(f"\n=== Auto-Index Validation Results ===\n")
    print(f"Total error codes in auto-index: {len(auto_index_codes)}")
    print(f"Total error code files: {len(file_codes)}")

    # Missing files
    if codes_in_auto_index_not_in_files:
        print(f"\n{len(codes_in_auto_index_not_in_files)} error codes in auto-index but missing files:")
        for code in sorted(codes_in_auto_index_not_in_files):
            print(f"  - {code}: {format_description(auto_index_codes.get(code))}")
    else:
        print("\nNo error codes are missing files. ✓")

    # Missing entries
    if codes_in_files_not_in_auto_index:
        print(f"\n{len(codes_in_files_not_in_auto_index)} error files without auto-index entries:")
        for code in sorted(codes_in_files_not_in_auto_index):
            print(f"  - {code}: {format_description(file_codes.get(code))}")
    else:
        print("\nNo error files are missing from the auto-index. ✓")

    # Description mismatches
    if description_mismatches:
        print(f"\n{len(description_mismatches)} description mismatches:")
        for code, auto_index_desc, file_desc in sorted(description_mismatches):
            print(f"\n  - {code}:")
            print(f"    Auto-Index: {format_description(auto_index_desc)}")
            print(f"    File      : {format_description(file_desc)}")

            if verbose:
                # Show exact differences for detailed debugging
                print("\n    Detailed differences:")
                differences = list(ndiff(auto_index_desc.splitlines(), file_desc.splitlines()))
                for line in differences:
                    if line.startswith('+ ') or line.startswith('- ') or line.startswith('? '):
                        print(f"      {line}")
    else:
        print("\nNo description mismatches found. ✓")

    # Role mismatches
    if role_mismatches:
        print(f"\n{len(role_mismatches)} page role mismatches:")
        for code, auto_index_role, file_role in sorted(role_mismatches):
            print(f"  - {code}:")
            print(f"    Auto-Index: {auto_index_role or 'MISSING'}")
            print(f"    File      : {file_role or 'MISSING'}")
    else:
        print("\nNo page role mismatches found. ✓")

    # Final status
    if not (codes_in_auto_index_not_in_files or codes_in_files_not_in_auto_index or
            description_mismatches or role_mismatches):
        print("\n✅ All validations passed! Auto-index is consistent with individual files.")
        return True
    else:
        print("\n❌ Validation failed.")
        return False

def main():
    parser = argparse.ArgumentParser(description='Validate auto-index.adoc against individual error files')
    parser.add_argument('--auto-index', help='Path to auto-index.adoc file')
    parser.add_argument('--dir', help='Path to directory containing error files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed differences for mismatches')
    args = parser.parse_args()

    # Get the script's directory
    script_dir = Path(__file__).parent.absolute()

    # Default paths if not specified
    errors_dir = args.dir if args.dir else script_dir.parent / 'modules' / 'ROOT' / 'pages' / 'errors' / 'gql-errors'
    auto_index_file = args.auto_index if args.auto_index else errors_dir / 'auto-index.adoc'

    # Validate that the paths exist
    if not os.path.exists(errors_dir):
        print(f"Error: Directory not found: {errors_dir}")
        return 1

    if not os.path.exists(auto_index_file):
        print(f"Error: Auto-index file not found: {auto_index_file}")
        return 1

    # Run validation
    success = validate_error_parity(errors_dir, auto_index_file, args.verbose)

    # Return 0 if success, 1 otherwise
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())