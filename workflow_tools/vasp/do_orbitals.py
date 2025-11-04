#!/usr/bin/env python3
"""
Script to generate orbital files using vaspkit from a VASP calculation.
"""

import argparse
from hmac import new
import re
import shutil
import subprocess
import sys
import os

def is_spin_polarized(filename="OUTCAR"):
    """Check if the VASP calculation is spin-polarized by reading OUTCAR."""
    try:
        with open(filename, 'r') as f:
            content = f.read()
            # Search for ISPIN pattern in OUTCAR
            match = re.search(r'ISPIN\s*=\s*(\d+)', content)
            if match:
                ispin = int(match.group(1))
                if ispin == 2:
                    return True
                else:
                    return False
            else:
                print(f"Error: ISPIN not found in {filename}")
                sys.exit(1)
    except FileNotFoundError:
        print(f"Error: {filename} file not found")
        sys.exit(1)
        
def extract_kpoints_names(kpoints, filename="KPOINTS"):
    """Extract kpoint names from KPOINTS file for the selected kpoints."""
    kpoint_names = []
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            # Skip the first 3 lines (header for manually set KPOINTS) 
            # and read all kpoint lines
            kpoint_lines = lines[3:]
            
            for kpoint in kpoints:
                # kpoint is 1-indexed, but array is 0-indexed
                line_index = kpoint - 1
                if line_index < len(kpoint_lines):
                    parts = kpoint_lines[line_index].split()
                    # Check if there is a 5th column (index 4) with kpoint name
                    if len(parts) >= 5:
                        kpoint_names.append(str(parts[4]))
                    else:
                        kpoint_names.append(str(kpoint))
                else:
                    if kpoint == 1:
                        kpoint_names.append("GAMMA")
                    else:
                        kpoint_names.append(str(kpoint))
    except FileNotFoundError:
        print(f"Error: {filename} file not found")
        sys.exit(1)
    return kpoint_names

def extract_nbands_and_nkpts(filename="OUTCAR"):
    """Extract NBANDS and NKPTS values from OUTCAR file."""
    try:
        with open(filename, 'r') as f:
            content = f.read()
            # Search for NBANDS pattern in OUTCAR
            match = re.search(r'NBANDS\s*=\s*(\d+)', content)
            if match:
                nbands = int(match.group(1))
            else:
                print(f"Error: NBANDS not found in {filename}")
                sys.exit(1)

            match = re.search(r'NKPTS\s*=\s*(\d+)', content)
            if match:
                nkpts = int(match.group(1))
            else:
                print(f"Error: NKPTS not found in {filename}")
                sys.exit(1)

            return nbands, nkpts
    except FileNotFoundError:
        print(f"Error: {filename} file not found")
        sys.exit(1)

def run_vaspkit_command(kpoint, band, input_data):
    """Run vaspkit command with specified kpoint and band."""
    try:
        # Run vaspkit command
        process = subprocess.Popen(['vaspkit'], 
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        stdout, stderr = process.communicate(input=input_data)
        
        if process.returncode != 0:
            print(f"Warning: vaspkit failed for kpoint {kpoint}, band {band}")
            print(f"Error: {stderr}")
            sys.exit(1)
        
    except FileNotFoundError:
        print("Error: vaspkit command not found. Make sure it's in your PATH.")
        sys.exit(1)

def main():
    starting_time = os.times()
    parser = argparse.ArgumentParser(description="Make orbitals using vaspkit from a VASP calculation.")
    
    # Extract NBANDS first to set default for bands
    nbands, nkpts = extract_nbands_and_nkpts()
    
    parser.add_argument('-b', '--bands', 
                       type=int, 
                       nargs='*', 
                       default=list(range(1, nbands + 1)),
                       help=f'List of band numbers (default: 1 to NBANDS ({nbands} here))')
    
    parser.add_argument('-k', '--kpoints', 
                       nargs='*', 
                       default=[1],
                       help=r"List of kpoint numbers or 'all' for all kpoints (default: gamma point (1))")

    parser.add_argument('-s', '--squared',
                        action='store_true',
                        help="Generate squared wavefunction files instead of real and imaginary parts.")

    parser.add_argument('-c', '-cube',
                        action='store_true',
                        help="Generate cube files instead of VASP files.")
    
    args = parser.parse_args()

    # Handle 'all' keyword for kpoints
    if args.kpoints == ['all']:
        args.kpoints = list(range(1, nkpts + 1))
    else:
        # Convert to integers
        try:
            args.kpoints = [int(k) for k in args.kpoints]
        except ValueError:
            print("Error: kpoints must be integers or 'all'")
            sys.exit(1)

    # Verify that provided kpoints are within range 1 to NKPTS
    if not all(1 <= kpoint <= nkpts for kpoint in args.kpoints):
        print(f"Error: KPOINTS must be between 1 and {nkpts}")
        sys.exit(1)

    kpoint_names = extract_kpoints_names(args.kpoints)

    print(f"NBANDS extracted from OUTCAR: {nbands}")
    print(f"Processing bands: {args.bands}")
    print(f"Processing kpoints: {kpoint_names}\n")
    
    # Process each combination of kpoint and band
    total_combinations = len(args.kpoints) * len(args.bands)
    current = 0

    for kpoint, kpoint_name in zip(args.kpoints, kpoint_names):
        for band in args.bands:
            current += 1
            # Progress bar
            progress = int(50 * current / total_combinations)
            bar = '█' * progress + '░' * (50 - progress)
            percent = 100 * current / total_combinations
            if current == 1:
                # first print: emit two lines
                print(f"kpoint {kpoint_name}, band {band}")
                print(f"[{bar}] {percent:.1f}% ({current}/{total_combinations})")
            else:
                # update the same two lines in-place using ANSI escapes
                # move cursor up 2 lines, clear line, then print updated lines
                sys.stdout.write("\033[2A")   # move cursor up 2 lines
                sys.stdout.write("\033[2K")   # clear entire line
                sys.stdout.write(f"kpoint {kpoint_name}, band {band}\n")
                sys.stdout.write("\033[2K")   # clear entire line
                sys.stdout.write(f"[{bar}] {percent:.1f}% ({current}/{total_combinations})\n")
                sys.stdout.flush()

            new_names = None
            if args.squared:
                if args.cube:
                    input_data = f"51\n516\n{kpoint}\n{band}\n"
                    if is_spin_polarized():
                        generated_files = [f"WFN_SQUARED_B{band:04d}_K{kpoint:04d}_{spin}.vasp.cube" for spin in ['UP', 'DW']]
                    else:
                        generated_files = [f"WFN_SQUARED_B{band:04d}_K{kpoint:04d}.vasp.cube"]
                else:
                    input_data = f"51\n515\n{kpoint}\n{band}\n"
                    if is_spin_polarized():
                        generated_files = [f"WF_SQUARED_B{band:04d}_K{kpoint:04d}_{spin}.vasp" 
                                           for spin in ['UP', 'DW']]
                    else:
                        generated_files = [f"WFN_SQUARED_B{band:04d}_K{kpoint:04d}.vasp"]
            else:
                if args.cube:
                    input_data = f"51\n512\n{kpoint}\n{band}\n"
                    if is_spin_polarized():
                        generated_files = [f"WFN_{part}_B{band:04d}_K{kpoint:04d}_{spin}.vasp.cube" 
                                           for spin in ['UP', 'DW'] for part in ['REAL', 'IMAG']]
                    else:
                        generated_files = [f"WFN_REAL_B{band:04d}_K{kpoint:04d}_UP.vasp.cube", # Probably an error in vaspkit naming 
                                           f"WFN_IMAG_B{band:04d}_K{kpoint:04d}.vasp.cube"] 
                        new_names = [f"WFN_REAL_B{band:04d}_{kpoint_name}.vasp.cube",
                                     f"WFN_IMAG_B{band:04d}_{kpoint_name}.vasp.cube"]
                else:
                    input_data = f"51\n511\n{kpoint}\n{band}\n"
                    if is_spin_polarized():
                        generated_files = [f"WF_{part}_B{band:04d}_K{kpoint:04d}_{spin}.vasp" 
                                           for spin in ['UP', 'DW'] for part in ['REAL', 'IMAG']]
                    else:
                        generated_files = [f"WFN_{part}_B{band:04d}_K{kpoint:04d}.vasp" 
                                           for part in ['REAL', 'IMAG']]
            run_vaspkit_command(kpoint, band, input_data)

            if not new_names:
                new_names = [generated_file.replace(f"K{kpoint:04d}", kpoint_name) for generated_file in generated_files]

            for generated_file, new_name in zip(generated_files, new_names):
                if generated_file != new_name:
                    try:
                        shutil.move(generated_file, new_name)
                    except FileNotFoundError:
                        print(f"Warning: Generated file {generated_file} not found, cannot rename to {new_name}")

    ending_time = os.times()
    runtime = ending_time[4] - starting_time[4]
    if runtime >= 60:
        minutes = int(runtime // 60)
        seconds = runtime % 60
        print(f"\nRuntime: {minutes} minutes and {seconds:.2f} seconds")
    else:
        print(f"\nRuntime: {runtime:.2f} seconds")

if __name__ == "__main__":
    main()
