
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

# Process each file in the gql-errors folder
for root, dirs, files in os.walk(gql_errors_folder):
    for file_name in files:
        file_path = os.path.join(root, file_name)

        # Read the content of the file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()

        # Check if 'ifndef' is present in the file
        if 'ifndef::backend-pdf[]' not in content:
            # Add the content_to_add at the end of the file
            content += "\n" + content_to_add

            # Write the updated content back to the file
            with open(file_path, 'w', encoding='utf-8', errors='ignore') as file:
                file.write(content)

print("Files updated successfully.")