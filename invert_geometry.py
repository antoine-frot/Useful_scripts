#!/usr/bin/env python3

import sys

def process_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    with open(filename, 'w') as f:
        for idx, line in enumerate(lines):
            if idx == 0 or idx ==1:
                f.write(line)  # Write the first line as is
            else:
                parts = line.split()
                inverted_parts = [parts[0]] + [str(-float(part)) for part in parts[1:]]
                f.write('  '.join(inverted_parts) + '\n')

def main(files):
    for file in files:
        try:
            process_file(file)
            print(f"File '{file}' processed successfully.")
        except Exception as e:
            print(f"Error processing file '{file}': {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./script_name.py <file1> <file2> ... <fileN>")
        sys.exit(1)
    
    files = sys.argv[1:]
    main(files)
