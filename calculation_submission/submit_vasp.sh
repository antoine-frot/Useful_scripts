#!/bin/bash

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
        exit 1
    fi

    relative_path=$(realpath --relative-to="$closest_dir" "$current_dir") # Extract the path segments from closest_dir to current_dir
    if [[ "$relative_path" == *-* ]]; then
        echo "Error: The directory '$(basename "$current_dir")' contains a hyphen (-)." >&2
        exit 1
    fi
    job_name=$(echo "$relative_path" | tr '/' '-') # Replace slashes with hyphens
    echo $job_name
}

### VASP_version
VASP_version_file=VASP_version.txt
if [ -f $VASP_version_file ]; then
    vasp_version=$(cat $VASP_version_file)
    echo "VASP version: $vasp_version"
else
    echo "Which VASP version?"
    available_versions=("6.5.0-impi" "6.4.3-gf-impi" "6.4.1" "6.3.2" "6.1.1_patched" "5.4.4-opt2")
    select version in "${available_versions[@]}"; do
        case $REPLY in
            1|2|3|4|5)
            vasp_version=Vasp6/vasp.$version
                break
                ;;
            6)
            vasp_version=Vasp5/vasp.$version
                break
                ;;
            *)
                echo "Invalid choice. Try again."
                ;;
        esac
    done
    echo $vasp_version > $VASP_version_file
fi
export vasp_version
job_name=$(get_job_name)
sbatch --job-name=$job_name /home/afrot/Useful_scripts/calculation_submission/sbatch_files/vasp_slurm.sh
