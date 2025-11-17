#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 <directory>"
    echo "Example: $0 directory_to_deprecate"
    exit 1
fi

for target_dir in "$@"; do
    if [ ! -d "$target_dir" ]; then
        echo "Error: '$target_dir' is not a valid directory."
        continue
    fi

    TARGET_REALPATH=$(realpath "$target_dir")
    HOME_REALPATH=$(realpath "$HOME")
    
    if [ "$TARGET_REALPATH" = "$HOME_REALPATH" ]; then
        echo "Error: Cannot deprecate the home directory itself."
        continue
    fi
    
    case "$TARGET_REALPATH" in
        "$HOME_REALPATH"/*) ;;
        *)
            echo "Error: Directory '$target_dir' is not inside the home directory."
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
done