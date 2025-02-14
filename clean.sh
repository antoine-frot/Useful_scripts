#!/bin/bash
: '
Purpose: delete all .err and .out file provided by slurm
'

for molecule in ${@:-Boranil*}; do
  for source_path in "${molecule}/${molecule}-"*; do
    rm "$source_path"/[0-9]*.out "$source_path"/[0-9]*.err
  done
done
