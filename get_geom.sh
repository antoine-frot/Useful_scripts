#!/bin/bash
: '
Usage: get_geom.sh GS|ES [molecule1 molecule2 ...]
Description:
  - Requires a state argument: "GS" (ground state) or "ES" (excited state).
  - If no molecule names are provided, defaults is all molecules (Boranil*).
  - Verifies that the current directory is "/home/$USER/Stage2025Tangui".
  - For each molecule, copies the optimized geometry of one state to the main directory
'
 
# Check for minimum arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 GS|ES [molecule1 molecule2 ... default=Boranil*]"
    exit 1
fi
 
# Validate state argument
state="$1"
if [[ "$state" != "GS" && "$state" != "ES" ]]; then
    echo "Error: First argument must be GS or ES."
    exit 1
fi
shift
 
# Set and verify target directory
target_dir="/home/$USER/Stage2025Tangui"
if [[ "$target_dir" != "$(pwd)" ]]; then
    echo "Error: Directory you're not in $target_dir."
    exit 1
fi
 
# Process each molecule
for molecule in ${@:-Boranil*}; do
    source_path="${molecule}/${molecule}-OPT${state}/${molecule}-OPT${state}.xyz"

    if [ ! -f "$source_path" ]; then
        echo "Warning: $source_path does not exist. Skipping."
        continue
    fi

   
    if cp "$source_path" "$molecule.xyz"; then
        echo "Copied: ${molecule}-OPT${state}.xyz"
    else
        echo "Error: Failed to copy $source_path"
    fi
done
