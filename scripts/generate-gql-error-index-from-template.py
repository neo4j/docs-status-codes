#!/usr/bin/env python3

import os
import re
from pathlib import Path
import argparse

# For debugging - examine a single file to understand its structure
def examine_error_file(file_path):
    """Print the contents of an error file for debugging."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            print(f"=== File Content for {file_path.name} ===")
            print(content)
            print("===================================")

            # Try to extract the description with different patterns
            patterns = [
                r'Status description::\s*(.*?)(?=\n\n|\n==|\Z)',
                r'== Status description\s*\n(.*?)(?=\n\n|\n==|\Z)',
                r'== Status description\s*\n\s*Status description:: (.*?)(?=\n\n|\n==|\Z)'
            ]

            for i, pattern in enumerate(patterns):
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    print(f"Pattern {i+1} matched! Description: {match.group(1)[:50]}...")
                else:
                    print(f"Pattern {i+1} did not match")
    except Exception as e:
        print(f"Error reading file: {e}")

def get_error_codes_from_files(errors_dir, verbose=False):
    """Get all error codes and their details from individual .adoc files."""
    error_codes = {}
    sample_file = None

    for file in os.listdir(errors_dir):
        if file.endswith('.adoc') and file != 'index.adoc' and file != 'auto-index.adoc':
            error_code = file[:-5]  # Remove .adoc extension
            file_path = os.path.join(errors_dir, file)

            if sample_file is None:
                sample_file = file_path  # Save first file for debugging

            # Extract details from file
            with open(file_path, 'r') as f:
                content = f.read()

                # Extract page role
                page_role = None
                role_match = re.search(r':page-role:\s*(.*?)(?=\n|\Z)', content)
                if role_match:
                    page_role = role_match.group(1).strip()

                # Extract description - try several patterns
                description = None
                desc_patterns = [
                    r'Status description::\s*(.*?)(?=\n\n|\n==|\Z)',  # Simple format
                    r'== Status description\s*\n\s*Status description:: (.*?)(?=\n\n|\n==|\Z)',  # Section + desc
                    r'== Status description\s*\n(.*?)(?=\n\n|\n==|\Z)'  # Section only
                ]

                for pattern in desc_patterns:
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        description = match.group(1).strip()
                        break

            error_codes[error_code] = {
                'description': description,
                'page_role': page_role
            }

            if verbose and description:
                print(f"Found description for {error_code}: {description[:50]}...")
            elif verbose:
                print(f"No description found for {error_code}")

    # If we didn't find any descriptions, examine a sample file
    if verbose and sample_file and not any(code['description'] for code in error_codes.values()):
        print("\nNo descriptions were found in any files. Examining a sample file:")
        examine_error_file(sample_file)

    return error_codes

def generate_from_template(template_file, errors_dir, output_file, include_descriptions=True, verbose=False):
    """Generate the index file from template and individual error files."""
    if verbose:
        print("Extracting error codes and descriptions...")

    # Get error codes and their info with improved extraction
    error_codes = get_error_codes_from_files(errors_dir, verbose)

    if verbose:
        desc_count = sum(1 for code in error_codes.values() if code['description'])
        print(f"Found {len(error_codes)} error code files, {desc_count} with descriptions")

    # Read the template
    with open(template_file, 'r') as f:
        template_content = f.read()

    # Define patterns to find placeholders
    patterns = [
        r'\{codes_starting_with:\'([^\']+)\'\}',
        r'\{codes-starting with: \'([^\']+)\'\}'
    ]

    # Replace placeholders with generated content
    for pattern in patterns:
        for match in re.finditer(pattern, template_content):
            prefix = match.group(1)
            placeholder = match.group(0)

            if verbose:
                print(f"Processing prefix: {prefix}")

            # Generate content for this prefix
            content = []
            matching_codes = [code for code in sorted(error_codes.keys()) if code.startswith(prefix)]

            for error_code in matching_codes:
                # Add page role if exists
                if error_codes[error_code]['page_role']:
                    content.append(f'[role=label--{error_codes[error_code]["page_role"]}]')

                content.append(f'=== xref:errors/gql-errors/{error_code}.adoc[{error_code}]')
                content.append('')

                # Add description if available and requested
                if include_descriptions and error_codes[error_code]['description']:
                    content.append(f'Status description:: {error_codes[error_code]["description"]}')
                    content.append('')

            section_content = '\n'.join(content)

            # Replace placeholder with generated content
            template_content = template_content.replace(placeholder, section_content)

    # Write the result to the output file
    with open(output_file, 'w') as f:
        f.write("// THIS IS AN AUTOMATICALLY GENERATED FILE. DO NOT EDIT IT. THE STRUCTURE IS GENERATED FROM templates/gql-index-template.adoc AND THE CODES ARE POPULATED BY THE SCRIPTS LOCATED IN THE scripts/ FOLDER.\n")
        f.write(template_content)

    print(f'Generated index file at: {output_file}')
    print(f'Used template: {template_file}')
    print(f'Total error codes processed: {len(error_codes)}')

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate GraphQL error code index from template')
    parser.add_argument('--no-descriptions', action='store_true',
                      help='If set, only error codes will be listed without their descriptions')
    parser.add_argument('--verbose', action='store_true',
                      help='Show detailed information during processing')
    parser.add_argument('--debug-file', help='Debug a specific error file')
    args = parser.parse_args()

    # Get the script's directory
    script_dir = Path(__file__).parent.absolute()

    # Navigate to the required directories
    errors_dir = script_dir.parent / 'modules' / 'ROOT' / 'pages' / 'errors' / 'gql-errors'
    template_file = script_dir.parent / 'modules' / 'ROOT' / 'templates' / 'gql-index-template.adoc'
    output_file = errors_dir / 'auto-index.adoc'

    # Debug specific file if requested
    if args.debug_file:
        debug_path = errors_dir / f"{args.debug_file}.adoc"
        if debug_path.exists():
            examine_error_file(debug_path)
        else:
            print(f"Error: Debug file not found at {debug_path}")
        return

    if not template_file.exists():
        print(f"Error: Template file not found at {template_file}")
        return

    generate_from_template(template_file, errors_dir, output_file,
                          not args.no_descriptions, args.verbose)

if __name__ == '__main__':
    main()