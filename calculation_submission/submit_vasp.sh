#!/bin/bash

# Function to check if any directory in the path contains a hyphen
check_for_hyphen() {
    local path="$1"
    IFS='/' read -ra dirs <<< "$path"
    for dir in "${dirs[@]}"; do
        if [[ "$dir" == *-* ]]; then
            echo "Error: The directory '$dir' contains a hyphen (-)." >&2
            exit 1
        fi
    done
}

# Navigate up and find the closest directory containing MAIN_DIR
current_dir=$(pwd)
closest_dir=""
temp_dir="$current_dir"
while [ "$temp_dir" != "/" ]; do
    if [ -f "$temp_dir/MAIN_DIR" ]; then
        closest_dir="$temp_dir"
        break
    fi
    temp_dir=$(dirname "$temp_dir")
done

if [ -z "$closest_dir" ]; then
    echo "Error: MAIN_DIR not found in any parent directory." >&2
    exit 1
fi

relative_path=$(realpath --relative-to="$closest_dir" "$current_dir") # Extract the path segments from closest_dir to current_dir
if [[ "$relative_path" == *-* ]]; then
    echo "Error: The directory '$(basename "$current_dir")' contains a hyphen (-)." >&2
    exit 1
fi
job_name=$(echo "$relative_path" | tr '/' '-') # Replace slashes with hyphens

sbatch --job-name=$job_name /home/afrot/Useful_scripts/calculation_submission/sbatch_files/vasp_slurm.sh
