"""
Convert enumlib struct_enum.out file to VASP POSCAR files.

This script parses the output from enumlib's structure enumeration and generates
individual POSCAR files for each enumerated structure. Each POSCAR is placed in
its own directory.

Vacancies are automatically excluded from the generated POSCAR files.

Usage:
    python enum_to_POSCAR.py

Input:
    struct_enum.out - Output file from enumlib containing enumerated structures

Output:
    POSCAR_XXX/POSCAR - Individual POSCAR files in separate directories
"""

import os
import numpy as np

def generate_poscars(input_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r') as f:
        lines = f.readlines()

    # 1. Parse Parent Lattice Vectors
    lattice_vectors = []
    for line_idx in range(3,6):
        line = lines[line_idx].strip()
        parts = line.split()
        lattice_vectors.append([float(parts[0]), float(parts[1]), float(parts[2])])

    # 2. Parse Number of Points and D-vectors
    num_d_vectors = int(lines[6].split()[0])
    d_vectors = []
    line_idx =7

    for _ in range(num_d_vectors):
        parts = lines[line_idx].strip().split()
        d_vectors.append([float(parts[0]), float(parts[1]), float(parts[2])])
        line_idx += 1
    d_vectors = np.array(d_vectors)

    # 3. Find the start of the structure table
    while "start" not in lines[line_idx]:
        line_idx += 1
    line_idx += 1 # Move past the header line

    # Count total structures to determine padding width
    total_structures = 0
    for i in range(line_idx, len(lines)):
        if lines[i].strip():
            total_structures += 1
    padding_width = len(str(total_structures))

    # 4. Parse each structure and write POSCAR
    struct_count = 0
    atom_names = ["Li", "Co", "O", "Vacancy"] # Placeholders for your 4-nary case

    for i in range(line_idx, len(lines)):
        line = lines[i].strip()
        if not line: continue
        
        parts = line.split()
        labeling = parts[-1]
        struct_idx = parts[0]
        
        # Determine atom types and counts (exclude vacancies)
        types = sorted(list(set(labeling)))
        # Filter out vacancy type (assuming '3' represents vacancy)
        types = [t for t in types if atom_names[int(t)] != "Vacancy"]
        grouped_atoms = {t: [] for t in types}
        
        for site_idx, atom_type in enumerate(labeling):
            if atom_names[int(atom_type)] != "Vacancy":
                grouped_atoms[atom_type].append(d_vectors[site_idx])

        # Write the POSCAR file with zero-padded index
        os.makedirs(f"POSCAR_{struct_idx.zfill(padding_width)}", exist_ok=True)
        filename = f"POSCAR_{struct_idx.zfill(padding_width)}/POSCAR"
        with open(filename, 'w') as p:
            p.write(f"Structure_{struct_idx} (from enumlib)\n")
            p.write("1.0\n")
            # Cell Vectors (Assuming cell size 1 for these HNFs)
            for v in lattice_vectors:
                p.write(f"  {v[0]:12.8f}  {v[1]:12.8f}  {v[2]:12.8f}\n")
            
            # Species names and counts
            p.write("  " + "  ".join([atom_names[int(t)] for t in types]) + "\n")
            p.write("  " + "  ".join([str(len(grouped_atoms[t])) for t in types]) + "\n")
            p.write("Cartesian\n")
            
            for t in types:
                for coord in grouped_atoms[t]:
                    p.write(f"  {coord[0]:12.8f}  {coord[1]:12.8f}  {coord[2]:12.8f}\n")
        
        struct_count += 1

    print(f"Successfully generated {struct_count} POSCAR files.")

if __name__ == "__main__":
    generate_poscars("struct_enum.out")