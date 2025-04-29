#!/usr/bin/env python3
"""
Script to extract processors and memory required by an orca input file values.
- Extracts the first MaxCore and nprocs in each job.
- Uses defaults (MaxCore=4000, nprocs=1) if either is missing in a job.
- Outputs the maximum nprocs and the maximum total memory (MaxCore * nprocs) across all jobs.
"""

import re
import sys

def find_values(filename):
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <filename>")
        sys.exit(1)
    
    try:
        max_nprocs, max_memory = find_values(sys.argv[1])
        print(max_nprocs, max_memory)
    except FileNotFoundError:
        print(f"Error: File '{sys.argv[1]}' not found.")
        sys.exit(1)
