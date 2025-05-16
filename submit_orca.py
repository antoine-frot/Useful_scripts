#!/usr/bin/env python3
"""
Module: submit_orca.py
Description:
    This script automates the preparation and submission of ORCA quantum chemical calculation jobs
    via SLURM. It expects exactly one input file (*.inp) and one or more geometry files (*.xyz) in
    the current directory.

    For each *.xyz file, the script will:
      - Create a dedicated directory (named after the geometry file without its extension).
      - Construct a job directory named by combining the *.xyz filename and the *.inp filename.
      - Copy and modify the input file: if the first "* xyzfile" line contains a .xyz file,
        it removes the old coordinate reference and appends the current .xyz filename.
      - Optionally insert directives to reuse previously calculated molecular orbitals if a
        corresponding *.gbw file is found.
      - Move the geometry file into the job directory.
      - Copy a SLURM submission script and submit the job.
      - Log the job submission in a designated log file.
    Finally, the original *.inp file is moved into an "Inputs" subdirectory.
    
Usage:
    Place one *.inp file and one or more *.xyz files in the working directory, then execute:
        python3 path/submit_orca.py
    (The coordinates in the input file should be specified as "* xyzfile", and multiple-step jobs are supported.)
"""

import os
import sys
import glob
import shutil
import subprocess
import re
from pathlib import Path

# --- Define Color Variables ---
class Colors:
    NC = '\033[0m'         # No Color
    R = '\033[0;31m'       # Red
    G = '\033[0;32m'       # Green
    Y = '\033[0;33m'       # Yellow
    M = '\033[0;35m'       # Magenta

# --- Set Variables ---
SCRIPT_DIR = "/home/afrot/script"
SUBMISSION_SCRIPT = os.path.join(SCRIPT_DIR, "orca_slurm.sh")
INPUT_DIRECTORY = 'Input_Orca'

def colored_print(color, message):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.NC}")

def prompt_yes_no(prompt):
    """
    Prompt user for yes/no input
    Args:
        prompt: The message to display
    Returns:
        bool: True for Yes, False for No
    """
    while True:
        answer = input(f"{Colors.Y}{prompt} (y/n)? {Colors.NC}").lower()
        if answer in ['y', 'yes']:
            return True
        elif answer in ['n', 'no']:
            return False
        else:
            colored_print(Colors.R, "Please answer y or n.")

def get_slurm_resources(input_file):
    """
    Get the number of processors and memory from the input file by calling an external Python script
    Args:
        input_file: Path to the ORCA input file
    Returns:
        tuple: (number of processors, memory)
    """
    script_path = os.path.join(SCRIPT_DIR, "get_slurm_procs_mem.py")
    try:
        result = subprocess.run(
            ["python3", script_path, input_file],
            capture_output=True,
            text=True,
            check=True
        )
        nprocs, memory = result.stdout.strip().split()
        return nprocs, memory
    except subprocess.CalledProcessError as e:
        colored_print(Colors.R, f"Error executing get_slurm_procs_mem.py: {e}")
        sys.exit(1)

def update_input_file(input_path, xyz_file):
    """
    Update the input file by modifying the xyz file reference
    Args:
        input_path: Path to the input file
        xyz_file: Name of the xyz file to use
    """
    with open(input_path, 'r') as file:
        lines = file.readlines()
    
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('* xyzfile'):
            # Remove existing xyz file reference if present
            parts = line.split()
            if any(part.endswith('.xyz') for part in parts):
                # Remove the last word if it ends with .xyz
                new_parts = []
                for part in parts:
                    if part.endswith('.xyz'):
                        continue
                    new_parts.append(part)
                lines[i] = ' '.join(new_parts) + f" {xyz_file}\n"
            else:
                # Just append the xyz file
                lines[i] = line.rstrip() + f" {xyz_file}\n"
            updated = True
            break
    
    if not updated:
        colored_print(Colors.R, f"Warning: No line starting with \"* xyzfile\" was found in {input_path}.")
        sys.exit(1)
    
    with open(input_path, 'w') as file:
        file.writelines(lines)

def main():
    """Main function to run the script"""
    # --- Set the Working Directory ---
    root_dir = os.getcwd()
    colored_print(Colors.Y, f"You are in the directory {root_dir}.")
    
    # --- Check for Required Input Files ---
    
    # Require exactly one *.inp file in the current directory
    inp_files = glob.glob("*.inp")
    if len(inp_files) != 1:
        colored_print(Colors.R, f"Error: Exactly one input file (*.inp) is expected in the current directory (currently {inp_files} are given).")
        sys.exit(1)
    input_file = inp_files[0]
    
    # Require at least one *.xyz file
    xyz_files = glob.glob("*.xyz")
    if len(xyz_files) == 0:
        colored_print(Colors.R, "Error: No xyz files found in the current directory.")
        sys.exit(1)
    
    # Inform the user about the number of .xyz files found
    if len(xyz_files) == 1:
        colored_print(Colors.G, f"Found 1 xyz file ({xyz_files[0]}).")
    else:
        colored_print(Colors.G, f"Found {Colors.M}{len(xyz_files)}{Colors.G} xyz files.")
    
    # --- Confirm Continuation ---
    if not prompt_yes_no("Do you want to continue"):
        colored_print(Colors.R, "Aborting.")
        sys.exit(1)
    colored_print(Colors.G, "Let's go!")
    
    # --- Initialize Flags ---
    two_existing_dir = True  # Indicates that at least one job directory already existed
    ask_overwrite = False    # Flag to stop prompting the user repeatedly
    ask_sameparameter = False  # Flag to stop prompting the user repeatedly
    overwrite_dirs = False   # Default value for overwriting directories
    submitted = 0
    
    # --- Process Each .xyz File ---
    for xyz_file in xyz_files:
        # Create a subdirectory named after the .xyz file (without its extension)
        molecule_no_ext = os.path.splitext(xyz_file)[0]
        xyz_dir = os.path.join(root_dir, molecule_no_ext.split('-')[0])
        os.makedirs(xyz_dir, exist_ok=True)
        
        # Enter the xyz_dir directory
        original_dir = os.getcwd()
        os.chdir(xyz_dir)
        
        # Construct job basename combining the .xyz filename and the input file name (both without extensions)
        inp_no_ext = os.path.splitext(input_file)[0]
        job_basename = f"{molecule_no_ext}-{inp_no_ext}"
        job_directory = os.path.join(os.getcwd(), job_basename)
        job_input = f"{job_basename}.inp"
        
        # If the job directory already exists, handle parameter reuse or prompt the user.
        if os.path.exists(job_directory):
            colored_print(Colors.R, f"Directory {os.path.basename(job_directory)} already exists.")
            
            # Ask the user if they want to keep the same response as just asked
            if not two_existing_dir and not ask_sameparameter:
                if prompt_yes_no("Do you want to keep the same parameter for all existing directories"):
                    ask_overwrite = True
                ask_sameparameter = True
            
            two_existing_dir = False
            
            # Ask before overwriting
            if not ask_overwrite:
                if prompt_yes_no("Do you want to overwrite the directory"):
                    overwrite_dirs = True
                else:
                    overwrite_dirs = False
            
            # Don't overwrite if asked
            if not overwrite_dirs:
                colored_print(Colors.Y, f"Skipping {xyz_file}.")
                os.chdir(original_dir)
                continue
        else:
            os.makedirs(job_directory, exist_ok=True)
        
        # Change to job directory
        os.chdir(job_directory)
        
        # Copy input file to job directory
        shutil.copy(os.path.join(root_dir, input_file), job_input)
        
        # --- Update the Input File with the Current .xyz File ---
        update_input_file(job_input, xyz_file)
        
        # Move the current .xyz file into the job directory
        shutil.copy(os.path.join(root_dir, xyz_file), job_directory)
        
        # --- Prepare and Submit the Job ---
        if not os.path.isfile(SUBMISSION_SCRIPT):
            colored_print(Colors.R, f"Submission script not found at {SUBMISSION_SCRIPT}.")
            os.chdir(original_dir)
            sys.exit(1)
        
        # Get the number of processor and the total memory from the input file
        nprocs, memory = get_slurm_resources(job_input)
        
        # Submit the job via SLURM
        try:
            subprocess.run([
                "sbatch",
                f"--job-name={job_basename}",
                f"--ntasks={nprocs}",
                f"--mem={memory}",
                SUBMISSION_SCRIPT,
                job_input
            ], check=True, capture_output=True)
            
            submitted += 1
            colored_print(Colors.G, f"{job_basename} has been submitted.")
            
            # Remove the original xyz file after successful submission
            os.remove(os.path.join(root_dir, xyz_file))
            
        except subprocess.CalledProcessError:
            colored_print(Colors.R, "Submitting the job failed. Exiting.")
            sys.exit(1)
        
        # Return to the original directory
        os.chdir(original_dir)
    
    if submitted == 0:
        colored_print(Colors.R, "No file submitted.")
        sys.exit(1)
    else:
        colored_print(Colors.G, f"{submitted} submitted successfully.")
    
    # Move the original *.inp file into an "Input_Orca" directory
    if prompt_yes_no("Do you want to keep the input file?"):
        os.makedirs(os.path.join(root_dir, INPUT_DIRECTORY), exist_ok=True)
        shutil.move(
            os.path.join(root_dir, input_file),
            os.path.join(root_dir, INPUT_DIRECTORY, input_file)
        )
        colored_print(Colors.G, f"{input_file} stored in {INPUT_DIRECTORY}.")
    else:
        os.remove(os.path.join(root_dir, input_file))

if __name__ == "__main__":
    main()