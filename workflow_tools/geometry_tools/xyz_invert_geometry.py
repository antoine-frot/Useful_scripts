#!/usr/bin/env python3
"""
Invert the geometry in .xyz file.
Usage:
    ./invert_geometry.py <file1> <file2> ... <fileN>
"""
import sys

def process_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    with open(filename, 'w') as f:
        for idx, line in enumerate(lines):
            if idx == 0 or idx ==1:
                f.write(line)  # First line is number of atoms, second line is title
            else:
                parts = line.split()
                inverted_parts = [parts[0]] + [str(-float(part)) for part in parts[1:]]
                f.write('  '.join(inverted_parts) + '\n')

def main(files):
    for file in files:
        try:
            process_file(file)
        except Exception as e:
            print(f"Error processing file '{file}': {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./script_name.py <file1> <file2> ... <fileN>")
        sys.exit(1)
    main(sys.argv[1:])
