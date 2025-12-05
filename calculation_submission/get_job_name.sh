#!/bin/bash
# Generates a job name based on the path from home directory to the current one.
# Replaces path separators with hyphens and validates that no hyphens exist
# in directory names to avoid job name conflicts.

get_job_name () {
    current_dir=$(pwd)
    relative_path=$(realpath --relative-to="$HOME" "$current_dir") # Extract the path segments from closest_dir to current_dir
    if [[ "$relative_path" == *-* ]]; then
        echo "Error: The directory '$(basename "$current_dir")' contains a hyphen (-)." >&2
        return 1
    fi
    job_name=$(echo "$relative_path" | tr '/' '-') # Replace slashes with hyphens
    echo $job_name
}
