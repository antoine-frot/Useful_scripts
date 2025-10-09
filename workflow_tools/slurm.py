#!/usr/bin/env python3
import os
import re
import subprocess
import sys

def find_latest_slurm_file():
    """Find the slurm-<integer>.out file with the highest integer."""
    pattern = re.compile(r'slurm-(\d+)\.out')
    max_num = -1
    max_file = None
    
    # Get all files in current directory
    try:
        files = os.listdir('.')
    except PermissionError:
        print("Error: Permission denied to read directory")
        sys.exit(1)
    
    # Find all matching files and track the highest number
    for filename in files:
        match = pattern.match(filename)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
                max_file = filename
    
    return max_file

def main():
    slurm_file = find_latest_slurm_file()
    
    if slurm_file is None:
        print("No slurm-*.out files found in current directory")
        sys.exit(1)
    
    # Open with vim
    try:
        subprocess.run(['vim', slurm_file])
    except FileNotFoundError:
        print("Error: vim not found. Please ensure vim is installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Error opening file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
