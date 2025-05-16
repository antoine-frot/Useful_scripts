#!/usr/bin/env python3
"""
ORCA Difference Density Generator

This script processes .gbw files from ORCA calculations to generate
difference density and organize them in a structured directory.

The script:
1. Processes .gbw files that don't start with digits (by default) or a specific file
2. Takes state numbers to plot as arguments (default: state 1)
3. Runs the ORCA plot command with appropriate input parameters
4. Moves resulting .nto files to an organized directory structure

Usage:
    ./plot_mos.py [filename.out] [state1 state2 ...]

Arguments:
    filename: Optional. Specific .out file to process. If not provided,
              processes all eligible .out files in the current directory.
    states:   Optional. List of state numbers to plot. Default: 1.

Requirements:
    - The path_orca environment variable must be set and pointing to ORCA installation
    - Must be run in a directory with the structure: /home/afrot/Stage2025Tangui/
    - .gbw files must exist in the current directory
"""
import os
import sys
import glob
import subprocess
import argparse
import shutil
import re

def main():
    parser = argparse.ArgumentParser(description='Generate difference densities from ORCA wavefunction file')
    parser.add_argument('filename', nargs='?', help='ORCA wavefunction to process')
    parser.add_argument('states', nargs='*', type=int, default=[1], 
                        help='States numbers to plot, give a list of blanks separated integers (default: 1)')
    args = parser.parse_args()
    
    extension = '.gbw'
    if args.filename:
        if not args.filename.endswith(f'{extension}'):
            print(f"Error: {args.filename} does not end with {extension}")
            sys.exit(1)
        files = [args.filename]
    else:
        files = [f for f in glob.glob(f"*{extension}") if not f[0].isdigit()]
        if len(files) > 1:
            for f in files:
                print(f"  - {f}")
            kept_file = input("Which file do you want to keep (0 for the first one, * for all): ")
            if kept_file.isdigit():
                kept_file_index = int(kept_file)
                files = [files[kept_file_index]]
            elif kept_file != "*":
                print("Warning: Input is not a digit or *")
                print("Aborting...")
                sys.exit(1)
            print("")

    
    if not files:
        print("No ORCA wavefunctions found to process.")
        sys.exit(1)
    
    print("Wavefunctions to process:")
    for f in files:
        print(f"  - {f}")
    print(f"States to plot: {args.states}")
    
    path_orca = os.environ.get('path_orca')
    if not path_orca:
        print("Error: environment variable 'path_orca' not found.")
        print("Please make sure it's defined in your shell (e.g., export path_orca=/path/to/orca)")
        sys.exit(1)
    
    for file in files:
        states_str = " ".join(map(str, args.states))
        input_content = f"6\ny\n{states_str}\n12"

        try:
            print(f"Processing {file}...")

            temp_script = f"temp_orca_script_{os.getpid()}.sh"
            with open(temp_script, 'w') as script:
                script.write(f'''#!/bin/bash
{path_orca}/orca_plot {file} -i << EOF > /dev/null 2>&1
6
y
{states_str}
12
EOF
''')

            os.chmod(temp_script, 0o755)
            result = subprocess.run(f"./{temp_script}", shell=True, capture_output=True, text=True)
            os.unlink(temp_script)

            if result.returncode != 0:
                print(f"Error processing {file} (code {result.returncode})")
                if result.stderr:
                    print(f"Error details: {result.stderr.strip()}")
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue
        
        # Move .nto files to the target directory
        current_dir = os.getcwd()
        dir_pattern = r'/home/afrot/Stage2025Tangui/(.*)'
        match = re.search(dir_pattern, current_dir)
        
        if match:
            sub_dir = match.group(1)
            
            target_dir = f"/home/afrot/Stage2025Tangui/MOs/{sub_dir}/"
            os.makedirs(target_dir, exist_ok=True)
            
            nto_files = glob.glob('*.cube')
            for nto_file in nto_files:
                target_path = os.path.join(target_dir, nto_file)
                shutil.move(nto_file, target_path)
            print("Moved .cube files")
        else:
            print("Current directory structure doesn't match expected pattern.")
            print(f"Current directory: {current_dir}")
            print("Not moving .cube files.")
    
    print("Processing completed.")

if __name__ == "__main__":
    main()
