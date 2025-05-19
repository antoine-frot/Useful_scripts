#!/bin/bash
: '
Purpose: get the required geometries to restart aborted calculations
'

# Check for minimum arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 GS|ES [pattern_in_the_error_file_names default=all]"
    exit 1
fi

# Validate state argument
state="$1"
if [[ "$state" != "GS" && "$state" != "ES" ]]; then
    echo "Error: First argument must be GS or ES."
    exit 1
fi
shift
script_path="/home/afrot/script"


for pattern in ${@:-.}
do
  echo "Processing pattern: $pattern"
  for molecule in $($script_path/error.sh | grep "$pattern" | awk -F'-' '{print $1}')
  do
    # Pass both state and molecule to get_geom
    $script_path/get_geom.sh "$state" "$molecule"
  done
done
