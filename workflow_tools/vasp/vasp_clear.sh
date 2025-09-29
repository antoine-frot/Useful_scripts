#!/bin/bash

# Ensure INPUTS is set and not empty
if [ -z "$INPUTS" ]; then
    echo "Error: \$INPUTS is not set or is empty."
    exit 1
fi

# Split INPUTS into an array (handles spaces in filenames if quoted)
IFS=' ' read -ra KEEP_FILES <<< "$INPUTS"

# Delete files not in KEEP_FILES
for file in *; do
    if [[ -f "$file" ]]; then
        if ! printf '%s\n' "${KEEP_FILES[@]}" | grep -qxF -- "$file"; then
            rm -f -- "$file"
        fi
    fi
done

