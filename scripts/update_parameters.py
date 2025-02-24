import re

# Define the path to the glossary.adoc file
glossary_file = "/Users/renetapopova/Git/docs-status-codes/modules/ROOT/partials/glossary.adoc"

# Read the content of the file
with open(glossary_file, 'r') as file:
    content = file.read()

# Define the regex pattern to match $parameter
pattern = re.compile(r'\$([A-Za-z0-9_]+)')

# Replace the matched pattern with { $parameter }
updated_content = pattern.sub(r'`{ $\1 }`', content)

# Write the updated content back to the file
with open(glossary_file, 'w') as file:
    file.write(updated_content)

print("File updated successfully.")