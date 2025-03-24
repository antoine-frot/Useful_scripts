#!/bin/bash
# Usage: ./remove.sh pattern_in_files pattern_to_remove
#
# This script renames files by removing a specific pattern from their names.

# Ensure exactly two arguments are provided.
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 pattern_in_files pattern_to_remove"
    exit 1
fi

# Assign arguments to variables for clarity
pattern_in_files="$1"
pattern_to_remove="$2"

# Find and rename files containing the specified pattern
for file in *"$pattern_in_files"*; do
    if [ -e "$file" ]; then
        new_file="${file/$pattern_to_remove/}"
        mv "$file" "$new_file"
        echo "Renamed '$file' to '$new_file'"
    else
        echo "No files found matching the pattern '$pattern_in_files'"
        exit 1
    fi
done

