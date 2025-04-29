#!/bin/bash
# Usage: ./rename_file.sh pattern_in_files pattern_to_replace [new_pattern]
#
# This script renames files by replacing or removing a specific pattern in their names.

# Ensure two or three arguments are provided.
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 pattern_in_files pattern_to_replace [new_pattern]"
    exit 1
fi

pattern_in_files="$1"
pattern_to_replace="$2"
new_pattern="${3:-}"

# Find and rename files containing the specified pattern
for file in *"$pattern_in_files"*; do
    if [ -e "$file" ]; then
        new_file="${file/$pattern_to_replace/$new_pattern}"
        mv "$file" "$new_file"
        echo "Renamed '$file' to '$new_file'"
    else
        echo "No files found matching the pattern '$pattern_in_files'"
        exit 1
    fi
done

