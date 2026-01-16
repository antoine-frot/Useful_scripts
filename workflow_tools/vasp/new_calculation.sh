#!/bin/bash
# Script to create new VASP calculation directories from an existing calculation

if [ $# -lt 1 ]; then
    echo "Usage: $0 <calculation_directory_1> <calculation_directory_2> ..."
    exit 1
fi

for calc_dir in "$@"; do
    mkdir -p $calc_dir
    cp $INPUTS $calc_dir
    cp CONTCAR $calc_dir/POSCAR
done