#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file_or_directory> [file_or_directory...]"
    echo "Example: $0 directory_to_deprecate file_to_deprecate.txt"
    exit 1
fi

for target in "$@"; do
    if [ ! -e "$target" ]; then
        echo "Error: '$target' does not exist."
        continue
    fi

    TARGET_REALPATH=$(realpath "$target")
    HOME_REALPATH=$(realpath "$HOME")
    
    if [ "$TARGET_REALPATH" = "$HOME_REALPATH" ]; then
        echo "Error: Cannot deprecate the home directory itself."
        continue
    fi
    
    case "$TARGET_REALPATH" in
        "$HOME_REALPATH"/*) ;;
        *)
            echo "Error: '$target' is not inside the home directory."
            continue
            ;;
    esac
    
    RELATIVE_PATH="${TARGET_REALPATH#$HOME_REALPATH/}"
    DEPRECATED_BASE="$HOME/deprecated"
    DEPRECATED_PATH="$DEPRECATED_BASE/$RELATIVE_PATH"
    mkdir -p "$(dirname "$DEPRECATED_PATH")"
    mv "$TARGET_REALPATH" "$DEPRECATED_PATH"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to move '$TARGET_REALPATH' to '$DEPRECATED_PATH'."
        continue
    fi
    
    echo "Successfully moved '$TARGET_REALPATH' to '$DEPRECATED_PATH'"
done