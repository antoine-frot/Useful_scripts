#!/bin/bash
: '
Purpose: look if an TURBOMOLE job finished succesfully
'

working_directory=$(pwd)
cd "/home/afrot/Stage2025Tangui"

for molecule in ${@:-*}; do
  if [ -d "$molecule" ]; then
    for source_path in "${molecule}/${molecule}-"*; do
      grep -H "****  ricc2 : all done  ****" "$source_path"/*.out 2>/dev/null | awk -F"/" '{print $(NF-1), $NF}'
    done
  fi
done

cd $working_directory

