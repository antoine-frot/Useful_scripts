import numpy as np
import sys

def read_xyz(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        num_atoms = int(lines[0].strip())
        coordinates = []
        for line in lines[2:num_atoms+2]:
            _, x, y, z = line.split()
            coordinates.append([float(x), float(y), float(z)])
    return np.array(coordinates)

def calculate_rmsd(coords1, coords2):
    if coords1.shape != coords2.shape:
        raise ValueError("The two structures must have the same number of atoms.")

    diff = coords1 - coords2
    rmsd = np.sqrt((diff ** 2).sum() / coords1.shape[0])
    return rmsd

def main(file1, file2):
    coords1 = read_xyz(file1)
    coords2 = read_xyz(file2)
    rmsd = calculate_rmsd(coords1, coords2)
    print(f"RMSD between the two structures: {rmsd:.4f} Å")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python calculate_rmsd.py <file1.xyz> <file2.xyz>")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    main(file1, file2)

