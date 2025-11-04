#!/usr/bin/env python3
"""
Script to rename PARCHG files by adding .vasp extension.
Changes files from PARCHG.band_number.kpoint_number to PARCHG.band_number.kpoint_number.vasp
"""

import os
import re
import argparse
import sys

def find_parchg_files(directory="."):
    """Find all PARCHG files matching the pattern PARCHG.band_number.kpoint_number"""
    parchg_pattern = re.compile(r'^PARCHG\.(\d{4})\.(\d{4})$')
    
    matching_files = []
    
    try:
        for filename in os.listdir(directory):
            match = parchg_pattern.match(filename)
            if match:
                matching_files.append(filename)
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied accessing directory '{directory}'")
        sys.exit(1)
    
    return matching_files

def rename_files(files, directory=".", dry_run=False):
    """Rename PARCHG files by adding .vasp extension"""
    
    if not files:
        print("No PARCHG files found matching the pattern.")
        return
    
    for filename in files:
        old_path = os.path.join(directory, filename)
        new_filename = f"{filename}.vasp"
        new_path = os.path.join(directory, new_filename)
        
        if dry_run:
            print(f"  {filename} -> {new_filename}")
            continue
            
        try:
            if os.path.exists(new_path):
                print(f"    Warning: {new_filename} already exists, skipping...")
                continue
                
            os.rename(old_path, new_path)
            
        except OSError as e:
            print(f"    Error renaming {filename}: {e}")
    
def main():
    parser = argparse.ArgumentParser(
        description="Rename PARCHG files by adding .vasp extension",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Rename files in current directory
  %(prog)s --dry-run         # Show what would be renamed without doing it
        """
    )
    
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Show what files would be renamed without actually renaming them')
    
    args = parser.parse_args()
    
    # Convert to absolute path for clarity
    directory = os.path.abspath(".")
    
    # Find matching files
    parchg_files = find_parchg_files(directory)
    
    # Rename files
    rename_files(parchg_files, directory, args.dry_run)

if __name__ == "__main__":
    main()