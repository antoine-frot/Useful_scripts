#!/bin/bash
if [ -f CONTCAR ]; then
    if [ ! -f POSCAR_ini ]; then
        mv POSCAR POSCAR_ini
        if [ $? -ne 0 ] || [ ! -f POSCAR_ini ]; then
            echo "Error: POSCAR file not found and cannot rename to POSCAR_ini. Aborting."
            exit 1
        fi
    fi
    cp CONTCAR POSCAR
    if [ $? -ne 0 ] || [ ! -f POSCAR ]; then
        echo "Error: Failed to create POSCAR from CONTCAR. Aborting."
        exit 1
    fi
fi
files=("OSZICAR" "OUTCAR" "XDATCAR")
# Saved each file with a the suffix corresponding to the slurm file (slurm-%j.out)
latest_slurm_file=$(ls -t slurm-*.out | head -n 1)
if [ -n "$latest_slurm_file" ]; then
    slurm_suffix="${latest_slurm_file#slurm-}"
    slurm_suffix="${slurm_suffix%.out}"
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "${file}_${slurm_suffix}"
        fi
    done
else
    echo "No slurm output files found. Skipping backup of files: ${files[@]}."
fi
submit_vasp
