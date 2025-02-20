#!/usr/bin/env python3
"""
Script to manage and submit ORCA jobs using SLURM.

This script automates the process of preparing and submitting ORCA jobs to a SLURM workload manager.
It handles the creation of job directories, copying of input files, and submission of jobs with
appropriate SLURM parameters. The script also supports a dry-run mode for testing without making
actual changes.

Key Features:
- Prompts the user for confirmation before proceeding with actions.
- Extracts SLURM parameters from ORCA input files.
- Handles existing job directories and GBW files.
- Submits jobs to SLURM with specified parameters.

Usage:
- Run the script from the specified ROOT_DIR.
- Ensure exactly one .inp file and at least one .xyz file are present in the ROOT_DIR.
- Use the --dry-run flag to test the script without making actual changes.

Dependencies:
- Requires Python 3.x and standard libraries (os, glob, shutil, subprocess, sys).
- Assumes the presence of a SLURM submission script (orca_slurm.sh) in the SCRIPT_DIR.
"""

import os
import glob
import shutil
import subprocess
import sys

# --- Define Color Variables ---
NC = '\033[0m'       # No Color
R = '\033[0;31m'     # Red
G = '\033[0;32m'     # Green
Y = '\033[0;33m'     # Yellow
M = '\033[0;35m'     # Magenta

# --- Configuration ---
SCRIPT_DIR = "/home/afrot/script"
ROOT_DIR = "/home/afrot/Stage2025Tangui"
INPUT_DIR_NAME = "Input_Orca"

def prompt_yes_no(question):
    """
    Prompts the user with a yes/no question and returns a boolean.

    Parameters:
    question (str): The question to display.

    Returns:
    bool: True for 'y' or 'yes', False for 'n' or 'no'.
    """
    while True:
        answer = input(f"{Y}{question} (y/n)? {NC}").strip().lower()
        if answer in ('y', 'yes'):
            return True
        elif answer in ('n', 'no'):
            return False
        print(f"{R}Please answer y or n.{NC}")

def get_slurm_params(filename):
    """
    Extracts the number of processors and memory required by an ORCA input file.

    Parameters:
    filename (str): Path to the ORCA input file.

    Returns:
    tuple: A tuple containing the number of processors and memory required.
    """
    with open(filename, 'r') as f:
        content = f.read()

    # Split content into job sections
    sections = re.split(r'\$new_job', content)
    all_pairs = []

    for section in sections:
        # Extract MaxCore and nprocs in current section
        maxcore_match = re.search(r'\bmaxcore\b\D*(\d+)', section, re.I)
        nprocs_match = re.search(r'\bnprocs\b\D*(\d+)', section, re.I)

        # Use defaults if not found
        maxcore = int(maxcore_match.group(1)) if maxcore_match else 4000
        nprocs = int(nprocs_match.group(1)) if nprocs_match else 1

        all_pairs.append((maxcore, nprocs))

    if not all_pairs:
        return (1, 4000)  # Both defaults if no sections
    
    max_nprocs = max(np for mc, np in all_pairs)
    max_memory = max(mc * np for mc, np in all_pairs)
    
    return (max_nprocs, max_memory)

def main():
    # --- Dry Run Flag ---
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print(f"{M}\n=== DRY RUN MODE === (No changes will be made){NC}\n")

    # --- Check Working Directory ---
    if os.getcwd() != ROOT_DIR:
        print(f"{R}Error: Please run script from {ROOT_DIR}{NC}")
        sys.exit(1)

    # --- Check Input Files ---
    inp_files = glob.glob('*.inp')
    if len(inp_files) != 1:
        print(f"{R}Error: Exactly one .inp file required{NC}")
        sys.exit(1)
    inp_file = inp_files[0]

    xyz_files = glob.glob('*.xyz')
    if not xyz_files:
        print(f"{R}Error: No .xyz files found{NC}")
        sys.exit(1)

    print(f"{G}Found {M}{len(xyz_files)}{G} XYZ files{NC}")

    if not prompt_yes_no("Continue"):
        print(f"{R}Aborted{NC}")
        sys.exit()

    # --- Process XYZ Files ---
    two_existing_dir = True  # At least one existing dir found?
    same_parameter = True    # Use same params for all existing dirs
    ask = False              # Stop prompting after first decision

    for xyz_path in xyz_files:
        xyz_file = os.path.basename(xyz_path)
        base_name = os.path.splitext(xyz_file)[0]
        
        # Create XYZ directory
        xyz_dir = os.path.join(ROOT_DIR, base_name)
        if dry_run:
            print(f"{M}Would create directory: {xyz_dir}{NC}")
        else:
            os.makedirs(xyz_dir, exist_ok=True)

        # Create job directory name
        job_base = f"{base_name}-{os.path.splitext(inp_file)[0]}"
        job_dir = os.path.join(xyz_dir, job_base)
        job_inp = os.path.join(job_dir, f"{job_base}.inp")

        # Handle existing directory
        dir_exists = os.path.exists(job_dir)
        if dir_exists:
            if not two_existing_dir and not ask:
                if prompt_yes_no("Apply same parameters to all existing directories"):
                    same_parameter = False
                ask = True
            two_existing_dir = False

            print(f"{R}Directory {job_base} exists{NC}")
            
            if same_parameter:
                if not prompt_yes_no("Overwrite directory"):
                    print(f"{R}Aborted{NC}")
                    sys.exit(1)
            
            if dry_run:
                print(f"{M}Would copy input file to: {job_inp}{NC}")
            else:
                shutil.copy(os.path.join(ROOT_DIR, inp_file), job_inp)
            
            # Check for existing GBW file
            gbw_file = os.path.join(job_dir, f"{job_base}.gbw")
            use_gbw = None
            if os.path.exists(gbw_file):
                use_gbw = f"{job_base}_use.gbw"
                if dry_run:
                    print(f"{M}Would copy GBW file to: {use_gbw}{NC}")
                else:
                    shutil.copy(gbw_file, os.path.join(job_dir, use_gbw))
                
                if dry_run:
                    print(f"{M}Would insert MOREAD directives in {job_inp}{NC}")
                else:
                    with open(job_inp, 'r') as f:
                        lines = f.readlines()
                    
                    insert_lines = [
                        "!MOREAD\n",
                        f"%moinp {use_gbw}\n"
                    ]
                    
                    for i, line in enumerate(lines):
                        if line.strip().startswith('* xyzfile'):
                            lines[i+1:i+1] = insert_lines
                            break
                    
                    with open(job_inp, 'w') as f:
                        f.writelines(lines)
        else:
            if dry_run:
                print(f"{M}Would create directory: {job_dir}{NC}")
                print(f"{M}Would copy input file to: {job_inp}{NC}")
            else:
                os.makedirs(job_dir)
                shutil.copy(os.path.join(ROOT_DIR, inp_file), job_inp)

        # Update XYZ reference in input file
        if dry_run:
            print(f"{M}Would update XYZ reference in {job_inp} to {xyz_file}{NC}")
        else:
            with open(job_inp, 'r') as f:
                lines = f.readlines()

            found = False
            for i, line in enumerate(lines):
                if line.strip().startswith('* xyzfile'):
                    parts = line.strip().split()
                    cleaned = [p for p in parts if not p.endswith('.xyz')]
                    lines[i] = ' '.join(cleaned) + f' {xyz_file}\n'
                    found = True
                    break
            
            if not found:
                print(f"{R}No * xyzfile line found in {job_inp}{NC}")
                sys.exit(1)

            with open(job_inp, 'w') as f:
                f.writelines(lines)

        # Move XYZ file to job directory
        if dry_run:
            print(f"{M}Would move {xyz_file} to {job_dir}{NC}")
        else:
            shutil.move(os.path.join(ROOT_DIR, xyz_file),
                        os.path.join(job_dir, xyz_file))

        # Submit SLURM job
        submission_script = os.path.join(SCRIPT_DIR, 'orca_slurm.sh')
        if not os.path.exists(submission_script):
            print(f"{R}Submission script missing{NC}")
            sys.exit(1)

        try:
            nprocs, memory = get_slurm_params(job_inp)
        except ValueError as e:
            print(e)
            sys.exit(1)

        if dry_run:
            print(f"{M}Would submit job with: sbatch --job-name {job_base} "
                  f"--ntasks {nprocs} --mem {memory}M {submission_script} {job_inp}{NC}")
        else:
            subprocess.run([
                'sbatch',
                '--job-name', job_base,
                '--ntasks', str(nprocs),
                '--mem', f'{memory}M',
                submission_script,
                job_inp
            ], stdout=subprocess.DEVNULL)

        print(f"{G}Submitted {job_base}{NC}")

    # Move original input file
    if prompt_yes_no("Keep input file"):
        input_dir = os.path.join(ROOT_DIR, INPUT_DIR_NAME)
        if dry_run:
            print(f"{M}Would move {inp_file} to {input_dir}{NC}")
        else:
            os.makedirs(input_dir, exist_ok=True)
            shutil.move(
                os.path.join(ROOT_DIR, inp_file),
                os.path.join(input_dir, inp_file)
    else:
        if dry_run:
            print(f"{M}Would delete {inp_file}{NC}")
        else:
            os.remove(os.path.join(ROOT_DIR, inp_file))

    print(f"{G}All jobs submitted successfully{NC}")
    if dry_run:
        print(f"{M}\n=== DRY RUN COMPLETE === (No actual changes made){NC}")

if __name__ == "__main__":
    main()
