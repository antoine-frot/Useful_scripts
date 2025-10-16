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
sbatch --job-name=$job_name /home/afrot/Useful_scripts/calculation_submission/sbatch_files/vasp_slurm.sh
