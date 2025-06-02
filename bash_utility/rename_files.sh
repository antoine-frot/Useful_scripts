#!/bin/bash
# Usage: ./rename_file.sh pattern_in_files pattern_to_replace [new_pattern]
#
# This script renames files by replacing or removing a specific pattern in their names.
# - pattern_in_files: Pattern to match files (e.g., "test" matches "test1.txt", "mytest.log")
# - pattern_to_replace: Pattern within filename to replace (e.g., "old" in "test_old_file.txt")
# - new_pattern: What to replace it with (optional, defaults to empty string for removal)

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Ensure two or three arguments are provided
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    basename=$( basename $0)
    echo "Usage: $basename pattern_in_files pattern_to_replace [new_pattern]"
    echo ""
    echo "Examples:"
    echo "  $basename 'test' 'old' 'new'      # Rename files containing 'test', replace 'old' with 'new'"
    echo "  $basename 'backup' '.bak'         # Remove '.bak' from files containing 'backup'"
    echo "  $basename '*.txt' 'draft' 'final' # Process all .txt files, replace 'draft' with 'final'"
    exit 1
fi

pattern_in_files="$1"
pattern_to_replace="$2"
new_pattern="${3:-}"

# Find files using pattern matching
shopt -s nullglob
matched_files=(*"$pattern_in_files"*)

# Check if any files were found
if [ ${#matched_files[@]} -eq 0 ]; then
    echo "No files found matching the pattern '$pattern_in_files'"
    exit 1
fi

# Process each matched file
for file in "${matched_files[@]}"; do
    
    # Skip if not a regular file (e.g., directories)
    if [ ! -f "$file" ]; then
        continue
    fi
    
    # Check if the file contains the pattern to replace
    if [[ "$file" != *"$pattern_to_replace"* ]]; then
        continue
    fi
    
    new_file="${file/$pattern_to_replace/$new_pattern}"
    
    # Skip if the new filename would be the same
    if [ "$file" = "$new_file" ]; then
        echo "Skipping '$file' (new name would be identical)"
        continue
    fi
    
    # Check if target file already exists
    if [ -e "$new_file" ]; then
        echo "Warning: Target file '$new_file' already exists. Skipping '$file'"
        continue
    fi
    
    # Perform the rename
    if mv "$file" "$new_file" 2>/dev/null; then
        echo "Renamed: '$file' → '$new_file'"
    else
        echo "Failed to rename: '$file' → '$new_file'"
    fi
done
