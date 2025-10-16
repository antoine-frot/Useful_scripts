#!/bin/bash
# get_job_name.sh - Generate job names for Slurm submissions
#
# Provides the get_job_name() function that generates a job name based on the
# relative path from the nearest MAIN_DIR file to the current directory.
# Replaces path separators with hyphens and validates that no hyphens exist
# in directory names to avoid job name conflicts.

get_job_name () {
    current_dir=$(pwd)
    closest_dir=""
    temp_dir="$current_dir"
# Navigate up and find the closest directory containing MAIN_DIR
    while [ "$temp_dir" != "/" ]; do
        if [ -f "$temp_dir/MAIN_DIR" ]; then
            closest_dir="$temp_dir"
            break
        fi
        temp_dir=$(dirname "$temp_dir")
    done

    if [ -z "$closest_dir" ]; then
        echo "Error: MAIN_DIR not found in any parent directory." >&2
        return 1
    fi

    relative_path=$(realpath --relative-to="$closest_dir" "$current_dir") # Extract the path segments from closest_dir to current_dir
    echo $relative_path
    if [[ "$relative_path" == *-* ]]; then
        echo "Error: The directory '$(basename "$current_dir")' contains a hyphen (-)." >&2
        return 1
    fi
    job_name=$(echo "$relative_path" | tr '/' '-') # Replace slashes with hyphens
    echo $job_name
}