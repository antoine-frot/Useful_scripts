#!/bin/bash
# Usage: ./rename_recursive.sh old_directory new_directory
#
# This script renames a directory from old_directory to new_directory.
# Then, it recursively renames any file or directory (within new_directory)
# whose name contains the old directory name by replacing that substring
# with the new directory name.

# Ensure exactly two arguments are provided.
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 old_directory new_directory"
    exit 1
fi

OLD_DIR="$1"
NEW_DIR="$2"

# Check that the old directory exists.
if [ ! -d "$OLD_DIR" ]; then
    echo "Error: Directory '$OLD_DIR' does not exist."
    exit 1
fi

# Rename the main directory.
mv "$OLD_DIR" "$NEW_DIR"
echo "Renamed directory '$OLD_DIR' to '$NEW_DIR'."

pushd "$NEW_DIR" > /dev/null
# Recursively process files and directories within the newly renamed directory.
# The -depth option ensures that files are renamed before their parent directories.
find . -depth -name "*$OLD_DIR*" | while IFS= read -r path; do
    parent_dir=$(dirname "$path")
    base_name=$(basename "$path")

    # Replace all occurrences of OLD_DIR in the basename with NEW_DIR.
    new_base_name="${base_name//$OLD_DIR/$NEW_DIR}"
    new_path="$parent_dir/$new_base_name"

    # Rename the file or directory.
    mv "$path" "$new_path"
done

popd > /dev/null
