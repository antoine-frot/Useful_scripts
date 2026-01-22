#!/bin/bash

source ${path_to_git}/calculation_submission/get_job_name.sh
job_name=$(get_job_name) || exit 1

### VASP_version
VASP_version_file=VASP_version.txt
if [ -f $VASP_version_file ]; then
    vasp_version=$(cat $VASP_version_file)
    echo "VASP version: $vasp_version"
else
    echo "Which VASP version?"
    available_versions=("6.5.1-impi-vtst" "6.5.0-impi" "6.4.3-gf-impi" "6.4.1" "6.3.2" "6.1.1_patched" "5.4.4-opt2")
    select version in "${available_versions[@]}"; do
        case $REPLY in
            1|2|3|4|5|6)
            vasp_version=Vasp6/vasp.$version
                break
                ;;
            7)
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

### Partition
Parition_file=Partition.txt
if [ -f $Parition_file ]; then
    partition=$(cat $Parition_file)
    echo "Partition: $partition"
else
    echo "Which partition?"
    available_partitions=("zen2" "zen4")
    select part in "${available_partitions[@]}"; do
        case $REPLY in
            1)
            partition="main"
                break
                ;;
            2)
            partition=$part
                break
                ;;
            *)
                echo "Invalid choice. Try again."
                ;;
        esac
    done
    echo $partition > $Parition_file
fi

# Submit VASP job and capture job ID
job_output=$(sbatch --job-name=$job_name --partition=$partition $path_to_git/calculation_submission/sbatch_files/vasp_slurm.sh)
vasp_job_id=$(echo $job_output | awk '{print $NF}')

# Wait for VASP job to complete and run post-processing
if [ ! -z "$vasp_job_id" ]; then
    (
        # Wait for job to finish
        while squeue -j $vasp_job_id 2>/dev/null | grep -q $vasp_job_id; do
            sleep 60
        done

        # Check if job completed successfully
        displayed_name="$job_name ($vasp_job_id)"
        submitted_file="$HOME/Submitted.txt"
        if grep -q "HURRAY: $displayed_name" $submitted_file; then
            # Run post-processing script
            vasp_do_bader
            if [[ $job_name == *"-fukui_plus" ]]; then
                $path_to_git/workflow_tools/vasp/bader/chgdiff.pl ../CHGCAR CHGCAR >/dev/null 2>&1 # First is reference CHGCAR
                mv CHGCAR_diff CHGCAR_fukui_plus
            elif [[ $job_name == *"-fukui_moins" ]]; then
                $path_to_git/workflow_tools/vasp/bader/chgdiff.pl CHGCAR ../CHGCAR >/dev/null 2>&1 # First is reference CHGCAR
                mv CHGCAR_diff CHGCAR_fukui_moins
            fi
        fi
    ) &
else
    echo "Failed to submit VASP job."
fi
