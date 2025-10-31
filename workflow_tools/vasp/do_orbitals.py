#!/usr/bin/env python3
"""
Script to generate orbital files using vaspkit from a VASP calculation.
"""

import argparse
import re
import shutil
import subprocess
import sys
import os

def extract_kpoints_names(kpoints, filename="KPOINTS"):
    """Extract kpoint names from KPOINTS file."""
    kpoint_names = [str(kpoint) for kpoint in kpoints]
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            # Skip the first 4 lines (header)
            for i, line in enumerate(lines[3:]):
                parts = line.split()
                # ensure there is a 5th column (index 4) before accessing it
                if len(parts) >= 5:
                    kpoint_names[i] = str(parts[4])
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

def run_vaspkit_command(kpoint, band):
    """Run vaspkit command with specified kpoint and band."""
    try:
        # Prepare input for vaspkit: 51, 511, kpoint, band
        input_data = f"51\n511\n{kpoint}\n{band}\n"
        
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
                       type=int, 
                       nargs='*', 
                       default=[1],
                       help=r"List of kpoint numbers (default: \gamma point (1))")

    args = parser.parse_args()

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

    orbital_files=[]
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
            run_vaspkit_command(kpoint, band)
            if kpoint_name != str(kpoint):
                shutil.move(f"WF_REAL_B{band:04d}_K{kpoint:04d}_UP.vasp",
                            f"WF_REAL_B{band:04d}_{kpoint_name}_UP.vasp")
                shutil.move(f"WF_REAL_B{band:04d}_K{kpoint:04d}_DW.vasp",
                            f"WF_REAL_B{band:04d}_{kpoint_name}_DW.vasp")
                orbital_files.append(f"WF_REAL_B{band:04d}_{kpoint_name}_UP.vasp")
            else:
                orbital_files.append(f"WF_REAL_B{band:04d}_K{kpoint:04d}_UP.vasp")

    ending_time = os.times()
    runtime = ending_time[4] - starting_time[4]
    if runtime >= 60:
        minutes = int(runtime // 60)
        seconds = runtime % 60
        print(f"\nRuntime: {minutes} minutes and {seconds:.2f} seconds")
    else:
        print(f"\nRuntime: {runtime:.2f} seconds")
            
    print("Run the following command to launch VESTA with generated orbitals:")
    vesta_command = "VESTA " + " ".join(orbital_files) + " 2>/dev/null &"
    print(vesta_command)

if __name__ == "__main__":
    main()
