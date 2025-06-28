#!/bin/bash

# Script to generate aliases for all scripts in a given directory
# Usage: ./generate_aliases.sh /path/to/scripts/directory

SCRIPT_DIR="${1:-$path_to_git}"  # Use first argument or default to ~/script

if [ ! -d "$SCRIPT_DIR" ]; then
    echo "Error: Directory '$SCRIPT_DIR' does not exist."
    echo "Usage: $0 /path/to/scripts/directory"
    exit 1
fi

SCRIPT_DIR=$(realpath "$SCRIPT_DIR")

# Function to determine the appropriate interpreter/command
get_command() {
    local file_path="$1"
    local filename=$(basename "$file_path")
    local ext="${filename##*.}"
    
    case "$ext" in
        py)
            echo "python3 $file_path"
            ;;
        sh|bash)
            echo "bash $file_path"
            ;;
        *)
            if [ -x "$file_path" ]; then
                echo "$file_path"
            else
                return 1
            fi
            ;;
    esac
}

# Generate aliases
for file in "$SCRIPT_DIR"/*; do
    [ ! -f "$file" ] && continue
    filename=$(basename "$file")
    
    [[ "$filename" =~ ^\. ]] && continue
    [[ "$filename" =~ ~$ ]] && continue
    [[ "$filename" =~ \.bak$ ]] && continue
    
    command=$(get_command "$file")
    [ $? -ne 0 ] && continue
    
    alias_name="${filename%.*}"
    [ -z "$alias_name" ] && continue
    
    echo "alias $alias_name='$command'"
done
echo ""
