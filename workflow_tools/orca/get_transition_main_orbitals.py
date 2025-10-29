#!/usr/bin/env python3
"""
Processes ORCA output file to extract transition orbitals and generate corresponding cube files.
"""

import argparse
import os
import subprocess
import sys
import shutil
from pathlib import Path
from get_properties.get_orbital_label import get_orbital_label
from get_properties.orca.get_HOMO import get_HOMO
from get_properties.orca.parse_transition import parse_canonical_transitions, parse_nto_transitions

def plot_orca_orbital(wavefunction_file, orbital_number):
    """Plot orbital number orbital_number thanks to orca_plot"""
    input_string = f"2\n{orbital_number}\n11\n12"
    
    try:
        process = subprocess.Popen(
            ['orca_plot', wavefunction_file, '-i'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=input_string)
        
        if process.returncode != 0:
            print(f"Error running orca_plot: {stderr}")
            sys.exit(1)
        return 
        
    except FileNotFoundError:
        print("Error: orca_plot command not found. Make sure ORCA is properly installed.")
        sys.exit(1)

def rename_and_move_cubes(wavefunction_file, initial_orbital, irred_rep1, final_orbital, irred_rep2, contribution, homo_idx):
    """Rename cube files and move to ../../MOs directory."""
    base_name = Path(wavefunction_file).stem
    
    # Get orbital labels
    first_label = get_orbital_label(initial_orbital, homo_idx)
    second_label = get_orbital_label(final_orbital, homo_idx)
    
    # Original filenames
    first_cube = f"{base_name}.mo{initial_orbital}{irred_rep1}.cube"
    second_cube = f"{base_name}.mo{final_orbital}{irred_rep2}.cube"
    
    # New filenames
    new_first = f"{base_name}.{first_label}{irred_rep1}.{contribution:.2f}.cube"
    new_second = f"{base_name}.{second_label}{irred_rep2}.{contribution:.2f}.cube"
    
    # Create target directory
    parts = os.getcwd().split('/')
    current_dir = '/'.join(parts[-2:])
    target_dir = Path(f"../../MOs/{current_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Rename and move files
    try:
        shutil.move(first_cube, target_dir / new_first)
        print(f"Moved {new_first}")
        shutil.move(second_cube, target_dir / new_second)
        print(f"Moved {new_second}")
            
    except OSError as e:
        print(f"Error moving files: {e}")

def main():
    parser = argparse.ArgumentParser(description="Processes ORCA output file to extract transition orbitals and generate corresponding cube files.")
    parser.add_argument("output_file", help="ORCA output file")
    parser.add_argument("states", nargs="*", type=int, default=[1], help="Space-separated list of states (default: [1])")
    parser.add_argument("-n", "--nto", action="store_true", help="Use natural transition orbital")
    
    args = parser.parse_args()
    
    if not args.states:
        args.states = [1]
    
    if not os.path.exists(args.output_file):
        print(f"Error: Output file {args.output_file} not found")
        return 1
    base_name = Path(args.output_file).stem.split('.')[0]
    
    homo_idx = get_HOMO(args.output_file)
    
    for state in args.states:
        print(f"Processing state {state}...")
        
        if args.nto:
            file_type = f"s{state}.nto"
            parse_function = parse_nto_transitions
        else:
            file_type = "gbw"
            parse_function = parse_canonical_transitions

        wavefunction_file = f"{base_name}.{file_type}"
        if not os.path.exists(wavefunction_file):
            print(f"Error: {wavefunction_file} not found")
            continue

        results = parse_function(args.output_file, state)
        if not results:
            print(f"No transitions found for state {state}")
            continue
        for result in results:
            initial_orbital, irred_rep1, final_orbital, irred_rep2, contribution = result

            plot_orca_orbital(wavefunction_file, initial_orbital)
            plot_orca_orbital(wavefunction_file, final_orbital)
            rename_and_move_cubes(wavefunction_file, initial_orbital, irred_rep1, final_orbital, irred_rep2, contribution, homo_idx)
    print('All done.')
    return 0


if __name__ == "__main__":
    sys.exit(main())
