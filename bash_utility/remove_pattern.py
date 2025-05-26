#!/usr/bin/env python3
"""
File Renamer Script

This script removes a specified pattern from filenames.
Usage: python remove_pattern.py [pattern] [files...]

Example:
    python remove_pattern.py "prefix_" file1.txt prefix_file2.txt
    This will rename prefix_file2.txt to file2.txt
"""

import os
import sys
import re

def remove_pattern_from_filename(filename, pattern):
    """Remove a pattern from a filename and return the new name."""
    # Get directory and base filename
    directory = os.path.dirname(filename)
    base_filename = os.path.basename(filename)
    
    # Remove the pattern from the base filename
    new_base_filename = re.sub(pattern, '', base_filename)
    
    # If nothing changed, return the original filename
    if new_base_filename == base_filename:
        return filename
    
    # Combine directory with new filename
    if directory:
        return os.path.join(directory, new_base_filename)
    else:
        return new_base_filename

def main():
    # Check arguments
    if len(sys.argv) < 3:
        print("Usage: python remove_pattern.py [pattern] [files...]")
        print("Example: python remove_pattern.py 'prefix_' file1.txt prefix_file2.txt")
        sys.exit(1)
    
    pattern = sys.argv[1]
    files = sys.argv[2:]
    
    renamed_count = 0
    for filename in files:
        if not os.path.exists(filename):
            print(f"Warning: '{filename}' does not exist. Skipping.")
            continue
        
        new_filename = remove_pattern_from_filename(filename, pattern)
        
        if new_filename != filename:
            try:
                # Check if target filename already exists to avoid overwriting
                if os.path.exists(new_filename):
                    print(f"Error: Cannot rename '{filename}' to '{new_filename}' - target already exists.")
                    continue
                
                os.rename(filename, new_filename)
                print(f"Renamed: '{filename}' -> '{new_filename}'")
                renamed_count += 1
            except Exception as e:
                print(f"Error renaming '{filename}': {e}")
    
    print(f"\nSummary: {renamed_count} file(s) renamed successfully.")

if __name__ == "__main__":
    main()
