#!/bin/bash
: '
Purpose: look if an orca job finished with an error
'

for molecule in ${@:-Boranil*}; do
  for source_path in "${molecule}/${molecule}-"*; do
    grep -H "ORCA finished by error termination" "$source_path"/"${molecule}"*.out | awk -F"/" '{print $NF}'
  done
done
