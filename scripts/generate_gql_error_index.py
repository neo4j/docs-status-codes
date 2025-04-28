#!/usr/bin/env python3

import os
import re
from collections import defaultdict
from pathlib import Path
import argparse

def read_error_file(file_path):
    """Read an error file and extract its description."""
    with open(file_path, 'r') as f:
        content = f.read()
        # Find the description after "Status description" heading
        match = re.search(r'== Status description\n(.*?)(?:\n\n|\Z)', content, re.DOTALL)
        if match:
            return match.group(1).strip()
    return None

def get_section_descriptions(index_file):
    """Extract section descriptions from the original index file.
    Only captures the text that appears immediately after a section heading and before any error codes."""
    section_descriptions = {}
    current_section = None
    description_lines = []

    with open(index_file, 'r') as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for section header
            section_match = re.match(r'^== ([^=\n]+)', line)
            if section_match:
                # If we have a previous section, save its description
                if current_section and description_lines:
                    section_descriptions[current_section] = '\n'.join(description_lines).strip()

                # Start new section
                current_section = section_match.group(1).strip()
                description_lines = []

                # Look ahead to collect description until we hit an error code entry or another section
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    # Stop if we hit an error code entry or another section
                    if next_line.startswith('===') or next_line.startswith('=='):
                        break
                    # Skip empty lines at the start
                    if not description_lines and not next_line:
                        j += 1
                        continue
                    # Add non-empty lines to description
                    if next_line and not next_line.startswith('//'):
                        description_lines.append(next_line)
                    # Stop at first empty line after we've started collecting description
                    elif description_lines:
                        break
                    j += 1

            i += 1

    # Don't forget the last section
    if current_section and description_lines:
        section_descriptions[current_section] = '\n'.join(description_lines).strip()

    return section_descriptions

def get_section_for_error_code(error_code):
    """Map error code to its section based on its prefix."""
    sections = {
        '08': 'Connection exceptions',
        '22': 'Data exceptions',
        '25': 'Invalid transaction state',
        '2D': 'Invalid transaction termination',
        '40': 'Transaction rollback',
        '42': 'Syntax error or access rule violation',
        '50': 'General processing exceptions',
        '51': 'System configuration or operation exceptions',
        '52': 'Procedure exceptions',
        '53': 'Function exceptions',
        'G1': 'Dependent object errors'
    }

    # Try to match the first two characters
    prefix = error_code[:2]
    return sections.get(prefix, 'General processing exceptions')  # Default to general if no match

def get_section_order():
    """Define the order in which sections should appear in the index."""
    return [
        'Connection exceptions',
        'Data exceptions',
        'Invalid transaction state',
        'Invalid transaction termination',
        'Transaction rollback',
        'Syntax error or access rule violation',
        'General processing exceptions',
        'System configuration or operation exceptions',
        'Procedure exceptions',
        'Function exceptions',
        'Dependent object errors'
    ]

def generate_anchor(section_name):
    """Generate an anchor tag from a section name.
    Converts to lowercase and replaces spaces with hyphens."""
    return f"[[{section_name.lower().replace(' ', '-')}]]"

def generate_index(errors_dir, output_file, original_index, include_descriptions=True):
    """Generate the index file from individual error files."""
    # Get section descriptions from original index
    section_descriptions = get_section_descriptions(original_index)

    # Get error codes and descriptions from files
    error_codes = {}
    for file in os.listdir(errors_dir):
        if file.endswith('.adoc') and file != 'index.adoc' and file != 'auto-index.adoc':
            error_code = file[:-5]  # Remove .adoc extension
            description = read_error_file(os.path.join(errors_dir, file)) if include_descriptions else None
            if include_descriptions and description:
                error_codes[error_code] = description
            elif not include_descriptions:
                error_codes[error_code] = None

    # Group error codes by section
    sections = defaultdict(list)
    for error_code in sorted(error_codes.keys()):
        section = get_section_for_error_code(error_code)
        sections[section].append(error_code)

    # Generate the index content
    content = []
    content.append(':description: This section describes the GQLSTATUS errors that Neo4j can return, grouped by category, and an example of when they can occur.')
    content.append('')
    content.append('[[neo4j-gqlstatus-errors]]')
    content.append('= List of GQLSTATUS error codes')
    content.append('')
    content.append('The following page provides an overview of all GQLSTATUS server error codes in Neo4j.')
    content.append('All errors in Neo4j have severity level `ERROR`.')
    content.append('')
    content.append('[WARNING]')
    content.append('====')
    content.append('Please note that while GQLSTATUS codes remain stable (any changes to them will be breaking), changes to status descriptions associated with these codes are not breaking and may happen at any time.')
    content.append('For this reason, parsing the status descriptions or incorporating them into scripts is not recommended.')
    content.append('====')
    content.append('')

    # Add sections in the defined order
    for section in get_section_order():
        if section in sections:
            # Add anchor before section heading
            content.append(generate_anchor(section))
            content.append(f'== {section}')
            content.append('')

            # Add section description if available
            if section in section_descriptions:
                description = section_descriptions[section]
                if description and description.strip():
                    content.append(description)
                    content.append('')

            # Add error codes for this section
            for error_code in sections[section]:
                content.append(f'=== xref:errors/gql-errors/{error_code}.adoc[{error_code}]')
                content.append('')
                if include_descriptions and error_codes[error_code]:
                    content.append(f'Status description:: {error_codes[error_code]}')
                    content.append('')

    # Add glossary section once at the end of the document (outside both loops)
    content.append('')
    content.append('ifndef::backend-pdf[]')
    content.append('[discrete.glossary]')
    content.append('== Glossary')
    content.append('')
    content.append('include::partial$glossary.adoc[]')
    content.append('endif::[]')

    # Write the index file
    with open(output_file, 'w') as f:
        f.write('\n'.join(content))

    print(f'Generated index file at: {output_file}')

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate GraphQL error code index')
    parser.add_argument('--no-descriptions', action='store_true',
                      help='If set, only error codes will be listed without their descriptions')
    args = parser.parse_args()

    # Get the script's directory
    script_dir = Path(__file__).parent.absolute()

    # Navigate to the gql-errors directory
    errors_dir = script_dir.parent / 'modules' / 'ROOT' / 'pages' / 'errors' / 'gql-errors'
    original_index = errors_dir / 'index.adoc'
    output_file = errors_dir / 'auto-index.adoc'

    if not original_index.exists():
        print("Error: Original index.adoc not found!")
        return

    generate_index(errors_dir, output_file, original_index, not args.no_descriptions)

if __name__ == '__main__':
    main()
