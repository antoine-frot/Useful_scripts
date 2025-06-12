#!/bin/bash
: '
Script: get_error.sh

Purpose:
--------
This script identifies and retrieves the necessary input and geometry files 
to restart aborted calculations. It processes directories based on patterns 
provided as arguments or defaults to processing all aborted calculations 
listed in the "Submited.txt" file. It only copies geometry files from calculations
with the same input to simplify resubmission.

Functionality:
--------------
1. Searches for calculations marked with "ERROR:" in the "Submited.txt" file.
2. Filters calculations based on optional patterns provided as arguments.
3. For each matching calculation:
   - Identifies the molecule and calculation method.
   - Copies the input file (e.g., ORCA or Turbomole input files) to the parent directory.
   - Finds and copies the geometry file (shortest `.xyz` filename) to the parent directory.
4. Outputs the number of files copied for each pattern.

Usage:
------
./get_error.sh [pattern1] [pattern2] ...

Arguments:
----------
- pattern: Optional. Filters calculations to process only those containing the specified pattern(s).

Output:
-------
- Copies input and geometry files to the parent directory.
- Displays warnings for missing directories or files.
- Prints the number of files copied for each pattern.

Dependencies:
-------------
- Requires "Submited.txt" to contain a list of calculations with "ERROR:" entries.
- Assumes calculations are organized in directories named as "<molecule>/<calculation>".

Example:
--------
To process all aborted calculations:
    ./get_error.sh

To process only calculations containing "pattern1" or "pattern2":
    ./get_error.sh pattern1 pattern2
'

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: ./get_error.sh [pattern1] [pattern2] ... (default: all)"
    exit 0
fi

get_input_file=0

for pattern in ${@:-""}
do
  if [[ $pattern != "" ]]; then
    echo "Processing pattern: $pattern"
  fi
  number_of_file_copied=0

  for calculation in $(grep "ERROR:" Submited.txt | awk -F': ' '{print $2}')
  do
    if [[ $calculation == *"$pattern"* ]]; then
      molecule=$(echo $calculation | awk -F'-' '{print $1}')
      if [ -z $calcul_method ]; then
        calcul_method=$(echo $calculation | awk -F'-' '{print $NF}')
        echo "Processing calcul method: $calcul_method"
      elif [[ $calcul_method != $(echo $calculation | awk -F'-' '{print $NF}') ]]; then
        continue
      fi

      if [[ -d $molecule/$calculation ]]; then
        pushd "$molecule/$calculation" >/dev/null

        if [ $get_input_file -eq 0 ]; then
          input_file_orca=$(ls *.inp 2>/dev/null)
          input_file_turbomole=$(ls *.input insert_*.txt sub_tm_psmn.sh 2>/dev/null)
          if [[ -n $input_file_orca ]]; then
            cp $input_file_orca ../../${input_file_orca##*-}
          elif [[ -n $input_file_turbomole ]]; then
            cp $input_file_turbomole ../../
          else
            echo "Warning: no input file found in $molecule/$calculation"
            echo "Aborting."
            exit 1
          fi
          get_input_file=1
        fi

        # Get the xyz file with the shortest filename
        shortest_xyz=$(find . -maxdepth 1 -name "*.xyz" -printf "%f\n" | awk '{ print length, $0 }' | sort -n | head -1 | cut -d' ' -f2-)

        if [[ -n $shortest_xyz && -f $shortest_xyz ]]; then
          cp "$shortest_xyz" ../../
          ((number_of_file_copied++))
        fi

        popd >/dev/null
      else
        echo "Warning: directory $molecule/$calculation not found"
      fi
    fi
  done

  echo "$number_of_file_copied files copied."
done

echo "All done."

