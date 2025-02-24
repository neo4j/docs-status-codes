import os

# Define the path to the gql-errors folder
gql_errors_folder = "modules/ROOT/pages/errors/gql-errors"

# Define the content to add
content_to_add = """ifndef::backend-pdf[]
[discrete.glossary]
== Glossary

include::partial$glossary.adoc[]
endif::[]
"""

# List to keep track of updated files
updated_files = []

# Process each file in the gql-errors folder
for root, dirs, files in os.walk(gql_errors_folder):
    for file_name in files:
        if file_name.endswith('.adoc'):
            file_path = os.path.join(root, file_name)

            # Read the content of the file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

            # Debug print to check if the file is read correctly
            print(f"Checking file: {file_path}")

            # Check if the specific pattern is present in the file
            if content_to_add not in content:
                # Debug print to check if the pattern is not found
                print(f"Pattern not found in file: {file_path}")

                # Add the content_to_add at the end of the file
                content += "\n" + content_to_add

                # Write the updated content back to the file
                with open(file_path, 'w', encoding='utf-8', errors='ignore') as file:
                    file.write(content)

                # Add the file to the list of updated files
                updated_files.append(file_path)
            else:
                # Debug print to check if the pattern is found
                print(f"Pattern already present in file: {file_path}")

# Print out all updated files
if updated_files:
    print("Updated files:")
    for file_path in updated_files:
        print(file_path)
else:
    print("No files were updated.")

print("Script execution completed.")