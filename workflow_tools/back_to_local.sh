#!/bin/bash

# Define the local computer (format: user@hostname or just hostname if same user)
LOCAL_COMPUTER="$USER@Coloquinte.d5.icgm.fr"

# Check if at least one argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 [file1] [file2] [dir1] ..."
    exit 1
fi

# Process each argument
for item in "$@"; do
    abs_path=$(realpath "$item")
    
    if [ ! -e "$abs_path" ]; then
        echo "Error: '$item' does not exist"
        continue
    fi
    
    parent_dir=$(dirname "$abs_path")
    
    # ssh key should be set up for passwordless access
    ssh "$LOCAL_COMPUTER" "mkdir -p '$parent_dir'"
    
    if [ -d "$abs_path" ]; then
        # If it's a directory, use rsync with trailing slash handling
        rsync -avz "$abs_path" "$LOCAL_COMPUTER:$parent_dir/"
    else
        # If it's a file, use scp
        scp "$abs_path" "$LOCAL_COMPUTER:$abs_path"
    fi
done