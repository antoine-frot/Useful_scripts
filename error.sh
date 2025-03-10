#!/bin/bash
: '
Purpose: look if an ORCA or TURBOMOLE job finished with an error
'

working_directory=$(pwd)
cd "/home/afrot/Stage2025Tangui"

for molecule in ${@:-*}; do
  if [ -d "$molecule" ]; then
    for source_path in "${molecule}/${molecule}-"*; do
      grep -H "ORCA finished by error termination" "$source_path"/"${molecule}"*.out 2>/dev/null | awk -F"/" '{print $NF}'
      grep -H "ended abnormally" "$source_path"/*.out 2>/dev/null | awk -F"/" '{print $(NF-1), $NF}'
    done
  fi
done

cd $working_directory
