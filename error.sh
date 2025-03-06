#!/bin/bash
: '
Purpose: look if an orca job finished with an error
'

working_directory=$(pwd)
cd "/home/afrot/Stage2025Tangui"

for molecule in ${@:-*}; do
  if [ -d "$molecule" ]; then
    for source_path in "${molecule}/${molecule}-"*; do
      grep -H "ORCA finished by error termination" "$source_path"/"${molecule}"*.out 2>/dev/null | awk -F"/" '{print $NF}'
    done
  fi
done

cd $working_directory
