#!/usr/bin/env python3
"""
Molecular Structure Comparison Tool

This script compares two molecular geometries from .xyz files using:
1. Optimal alignment (Kabsch algorithm) to handle rotations/translations
2. Root Mean Square Deviation (RMSD) calculation
3. Heavy-atom RMSD (ignoring hydrogens)
4. Enantiomer detection (mirror image structures)
5. Chemical bond analysis and geometric descriptors

Usage: python compare_structures.py structure1.xyz structure2.xyz
"""

import numpy as np
import argparse
import sys
from pathlib import Path

def read_xyz_file(filename):
    """
    Read an XYZ file and return atomic symbols and coordinates.
    
    Args:
        filename (str): Path to the XYZ file
        
    Returns:
        tuple: (symbols, coordinates) where symbols is a list of atomic symbols
               and coordinates is a numpy array of shape (n_atoms, 3)
    """
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # First line contains number of atoms
        n_atoms = int(lines[0].strip())
        
        # Second line is typically a comment (skip)
        # Remaining lines contain atomic data
        symbols = []
        coordinates = []
        
        for i in range(2, 2 + n_atoms):
            parts = lines[i].strip().split()
            symbols.append(parts[0])
            coordinates.append([float(parts[1]), float(parts[2]), float(parts[3])])
        
        return symbols, np.array(coordinates)
    
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        sys.exit(1)

def center_coordinates(coords):
    """
    Center coordinates by subtracting the centroid.
    
    Args:
        coords (np.ndarray): Coordinates array of shape (n_atoms, 3)
        
    Returns:
        np.ndarray: Centered coordinates
    """
    centroid = np.mean(coords, axis=0)
    return coords - centroid

def kabsch_algorithm(P, Q, allow_reflection=False):
    """
    Apply Kabsch algorithm to find optimal rotation matrix.
    
    Args:
        P (np.ndarray): Reference coordinates (n_atoms, 3)
        Q (np.ndarray): Coordinates to align (n_atoms, 3)
        allow_reflection (bool): Whether to allow reflection to minimize RMSD
        
    Returns:
        tuple: (rotation_matrix, aligned_Q, is_reflection)
    """
    P_centered = center_coordinates(P)
    Q_centered = center_coordinates(Q)
    
    H = Q_centered.T @ P_centered
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    
    # Check if we have a reflection (det(R) = -1)
    is_reflection = False
    if np.linalg.det(R) < 0:
        is_reflection = True
        if not allow_reflection:
            # Force proper rotation by flipping the last column of Vt
            Vt[-1, :] *= -1
            R = Vt.T @ U.T
    
    # Apply transformation to centered coordinates
    Q_aligned = Q_centered @ R.T
    
    return R, Q_aligned + np.mean(P, axis=0), is_reflection

def calculate_rmsd(coords1, coords2):
    """
    Calculate Root Mean Square Deviation between two coordinate sets.
    
    Args:
        coords1 (np.ndarray): First set of coordinates
        coords2 (np.ndarray): Second set of coordinates
        
    Returns:
        float: RMSD value in Angstroms
    """
    diff = coords1 - coords2
    return np.sqrt(np.mean(np.sum(diff**2, axis=1)))

def calculate_heavy_atom_rmsd(symbols, coords1, coords2):
    """
    Calculate RMSD considering only heavy atoms (non-hydrogen).
    
    Args:
        symbols (list): List of atomic symbols
        coords1 (np.ndarray): First set of coordinates
        coords2 (np.ndarray): Second set of coordinates
        
    Returns:
        tuple: (heavy_atom_rmsd, n_heavy_atoms)
    """
    heavy_indices = np.array([i for i, symbol in enumerate(symbols) if symbol.upper() != 'H'])
    
    if len(heavy_indices) == 0:
        return 0.0, 0
    
    heavy_coords1 = coords1[heavy_indices]
    heavy_coords2 = coords2[heavy_indices]
    
    heavy_rmsd = calculate_rmsd(heavy_coords1, heavy_coords2)
    
    return heavy_rmsd, len(heavy_indices)

def get_covalent_radius(element):
    """
    Get approximate covalent radius for common elements (in Angstroms).
    
    Args:
        element (str): Element symbol
        
    Returns:
        float: Covalent radius in Angstroms
    """
    # Covalent radii for common elements
    radii = {
        'H': 0.31, 'He': 0.28,
        'Li': 1.28, 'Be': 0.96, 'B': 0.84, 'C': 0.76, 'N': 0.71, 'O': 0.66, 'F': 0.57, 'Ne': 0.58,
        'Na': 1.66, 'Mg': 1.41, 'Al': 1.21, 'Si': 1.11, 'P': 1.07, 'S': 1.05, 'Cl': 1.02, 'Ar': 1.06,
        'K': 2.03, 'Ca': 1.76, 'Sc': 1.70, 'Ti': 1.60, 'V': 1.53, 'Cr': 1.39, 'Mn': 1.39, 'Fe': 1.32,
        'Co': 1.26, 'Ni': 1.24, 'Cu': 1.32, 'Zn': 1.22, 'Ga': 1.22, 'Ge': 1.20, 'As': 1.19, 'Se': 1.20,
        'Br': 1.20, 'Kr': 1.16
    }
    return radii.get(element, 1.5)  # Default to 1.5 Å if element not found

def identify_bonds(symbols, coords, bond_tolerance=0.4):
    """
    Identify chemical bonds based on distance criteria.
    
    Args:
        symbols (list): List of atomic symbols
        coords (np.ndarray): Coordinates of shape (n_atoms, 3)
        bond_tolerance (float): Additional tolerance beyond sum of covalent radii
        
    Returns:
        list: List of tuples (i, j, distance) representing bonds
    """
    bonds = []
    n_atoms = len(coords)
    
    for i in range(n_atoms):
        for j in range(i+1, n_atoms):
            distance = np.linalg.norm(coords[i] - coords[j])
            
            # Check if distance is within bonding range
            expected_bond_length = get_covalent_radius(symbols[i]) + get_covalent_radius(symbols[j])
            max_bond_distance = expected_bond_length + bond_tolerance
            min_bond_distance = expected_bond_length * 0.5  # Minimum reasonable bond length
            
            if min_bond_distance <= distance <= max_bond_distance:
                bonds.append((i, j, distance))
    
    return bonds

def calculate_all_distances(coords):
    """
    Calculate all pairwise atomic distances (not bonds).
    
    Args:
        coords (np.ndarray): Coordinates of shape (n_atoms, 3)
        
    Returns:
        np.ndarray: Distance matrix
    """
    n_atoms = len(coords)
    distances = np.zeros((n_atoms, n_atoms))
    
    for i in range(n_atoms):
        for j in range(i+1, n_atoms):
            dist = np.linalg.norm(coords[i] - coords[j])
            distances[i, j] = distances[j, i] = dist
    
    return distances

def compare_actual_bonds(bonds1, bonds2, symbols1, symbols2, tolerance=0.01):
    """
    Compare actual chemical bonds between two structures.
    
    Args:
        bonds1, bonds2 (list): Lists of bonds (i, j, distance)
        symbols1, symbols2 (list): Atomic symbols
        tolerance (float): Tolerance for considering bond lengths equal
        
    Returns:
        dict: Dictionary with bond comparison results
    """
    # Convert bonds to sets of atom pairs for comparison
    pairs1 = {(min(symbols1[i], symbols1[j]), max(symbols1[i], symbols1[j]), i, j) for i, j, _ in bonds1}
    pairs2 = {(min(symbols2[i], symbols2[j]), max(symbols2[i], symbols2[j]), i, j) for i, j, _ in bonds2}
    
    # Create dictionaries for easy lookup
    bonds1_dict = {(i, j): dist for i, j, dist in bonds1}
    bonds2_dict = {(i, j): dist for i, j, dist in bonds2}
    
    common_bonds = 0
    bond_length_differences = []
    missing_in_2 = 0
    missing_in_1 = 0
    
    # Check bonds in structure 1
    for i, j, dist1 in bonds1:
        if (i, j) in bonds2_dict:
            dist2 = bonds2_dict[(i, j)]
            bond_length_differences.append(abs(dist1 - dist2))
            common_bonds += 1
        elif (j, i) in bonds2_dict:
            dist2 = bonds2_dict[(j, i)]
            bond_length_differences.append(abs(dist1 - dist2))
            common_bonds += 1
        else:
            missing_in_2 += 1
    
    # Check for bonds in structure 2 not in structure 1
    for i, j, _ in bonds2:
        if (i, j) not in bonds1_dict and (j, i) not in bonds1_dict:
            missing_in_1 += 1
    
    result = {
        'total_bonds_1': len(bonds1),
        'total_bonds_2': len(bonds2),
        'common_bonds': common_bonds,
        'missing_in_structure_2': missing_in_2,
        'missing_in_structure_1': missing_in_1,
        'max_bond_length_diff': max(bond_length_differences) if bond_length_differences else 0,
        'mean_bond_length_diff': np.mean(bond_length_differences) if bond_length_differences else 0,
        'bonds_with_large_diff': sum(1 for diff in bond_length_differences if diff > tolerance)
    }
    
    return result

def compare_distance_matrices(dist1, dist2, tolerance=0.01):
    """
    Compare all pairwise distance matrices (for structural similarity).
    
    Args:
        dist1, dist2 (np.ndarray): Distance matrices
        tolerance (float): Tolerance for considering distances equal
        
    Returns:
        tuple: (max_difference, mean_difference, large_differences_count)
    """
    diff = np.abs(dist1 - dist2)
    max_diff = np.max(diff)
    mean_diff = np.mean(diff[np.triu_indices_from(diff, k=1)])
    large_diffs = np.sum(diff > tolerance)
    
    return max_diff, mean_diff, large_diffs

def detect_enantiomers(coords1, coords2, symbols):
    """
    Detect if two structures are enantiomers (mirror images).
    
    Args:
        coords1, coords2 (np.ndarray): Coordinate arrays
        symbols (list): Atomic symbols
        
    Returns:
        dict: Information about enantiomer relationship
    """
    # Try alignment without allowing reflection
    R_no_refl, coords2_aligned_no_refl, _ = kabsch_algorithm(coords1, coords2, allow_reflection=False)
    rmsd_no_refl = calculate_rmsd(coords1, coords2_aligned_no_refl)
    
    # Try alignment allowing reflection
    R_refl, coords2_aligned_refl, is_reflection = kabsch_algorithm(coords1, coords2, allow_reflection=True)
    rmsd_refl = calculate_rmsd(coords1, coords2_aligned_refl)
    
    return {
        'rmsd_rotation_only': rmsd_no_refl,
        'rmsd_with_reflection': rmsd_refl,
        'is_enantiomer': is_reflection and rmsd_refl < 0.01,
        'reflection_improves_alignment': rmsd_refl < rmsd_no_refl * 0.5,
        'best_aligned_coords': coords2_aligned_refl if rmsd_refl < rmsd_no_refl else coords2_aligned_no_refl,
        'transformation_matrix': R_refl if rmsd_refl < rmsd_no_refl else R_no_refl,
        'used_reflection': rmsd_refl < rmsd_no_refl
    }

def main():
    parser = argparse.ArgumentParser(description='Compare two molecular structures from XYZ files')
    parser.add_argument('file1', help='First XYZ file')
    parser.add_argument('file2', help='Second XYZ file')
    parser.add_argument('--tolerance', type=float, default=0.01, 
                       help='Tolerance for distance comparison (default: 0.01 Å)')
    parser.add_argument('--bond-tolerance', type=float, default=0.4,
                       help='Additional tolerance for bond identification beyond covalent radii (default: 0.4 Å)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    for filename in [args.file1, args.file2]:
        if not Path(filename).exists():
            print(f"Error: File {filename} not found")
            sys.exit(1)
    
    symbols1, coords1 = read_xyz_file(args.file1)
    symbols2, coords2 = read_xyz_file(args.file2)
    
    if len(symbols1) != len(symbols2):
        print(f"Error: Different number of atoms ({len(symbols1)} vs {len(symbols2)})")
        sys.exit(1)
    
    if symbols1 != symbols2:
        print("Warning: Atomic symbols don't match exactly")
        if args.verbose:
            for i, (s1, s2) in enumerate(zip(symbols1, symbols2)):
                if s1 != s2:
                    print(f"  Atom {i+1}: {s1} vs {s2}")
    
    
    rmsd_before = calculate_rmsd(coords1, coords2)
    print(f"\nRMSD before alignment: {rmsd_before:.4f} Å")
    
    enantiomer_analysis = detect_enantiomers(coords1, coords2, symbols1)
    
    coords2_aligned = enantiomer_analysis['best_aligned_coords']
    rotation_matrix = enantiomer_analysis['transformation_matrix']
    
    rmsd_after = calculate_rmsd(coords1, coords2_aligned)
    print(f"RMSD after optimal alignment: {rmsd_after:.4f} Å")
    
    # Calculate heavy-atom RMSD
    heavy_rmsd, n_heavy = calculate_heavy_atom_rmsd(symbols1, coords1, coords2_aligned)
    n_hydrogen = len(symbols1) - n_heavy
    
    print(f"Heavy-atom RMSD (ignoring H): {heavy_rmsd:.4f} Å ({n_heavy} heavy atoms, {n_hydrogen} hydrogens)")
    
    if enantiomer_analysis['is_enantiomer']:
        print("⚠️  ENANTIOMER DETECTED: Structures are mirror images!")
        print(f"   RMSD with rotation only: {enantiomer_analysis['rmsd_rotation_only']:.4f} Å")
        print(f"   RMSD with reflection: {enantiomer_analysis['rmsd_with_reflection']:.4f} Å")
    elif enantiomer_analysis['reflection_improves_alignment']:
        print("⚠️  REFLECTION IMPROVES ALIGNMENT: Possible enantiomers or inverted structure")
        print(f"   RMSD with rotation only: {enantiomer_analysis['rmsd_rotation_only']:.4f} Å")
        print(f"   RMSD with reflection: {enantiomer_analysis['rmsd_with_reflection']:.4f} Å")
    
    if args.verbose:
        transformation_type = "Rotation + Reflection" if enantiomer_analysis['used_reflection'] else "Rotation only"
        print(f"\nTransformation used: {transformation_type}")
        print(f"Transformation matrix:")
        for row in rotation_matrix:
            print(f"  [{row[0]:8.4f} {row[1]:8.4f} {row[2]:8.4f}]")
    
    bonds2_aligned = identify_bonds(symbols2, coords2_aligned, args.bond_tolerance)
    
    bonds1 = identify_bonds(symbols1, coords1, args.bond_tolerance)
    bonds2 = identify_bonds(symbols2, coords2, args.bond_tolerance)
    
    if args.verbose:
        print(f"\nBonds in structure 1:")
        for i, j, dist in bonds1:
            print(f"  {symbols1[i]}{i+1}-{symbols1[j]}{j+1}: {dist:.3f} Å")
    
    bond_comparison = compare_actual_bonds(bonds1, bonds2_aligned, symbols1, symbols2, args.tolerance)
    
    print(f"\nChemical bond analysis:")
    #print(f"  Bonds in structure 1: {bond_comparison['total_bonds_1']}")
    #print(f"  Bonds in structure 2: {bond_comparison['total_bonds_2']}")
    #print(f"  Common bonds: {bond_comparison['common_bonds']}")
    #print(f"  Missing in structure 2: {bond_comparison['missing_in_structure_2']}")
    #print(f"  Missing in structure 1: {bond_comparison['missing_in_structure_1']}")
    print(f"  Max bond length difference: {bond_comparison['max_bond_length_diff']:.4f} Å")
    print(f"  Mean bond length difference: {bond_comparison['mean_bond_length_diff']:.4f} Å")
    print(f"  Bonds with difference >{args.tolerance} Å: {bond_comparison['bonds_with_large_diff']}")
    
    dist1 = calculate_all_distances(coords1)
    dist2_aligned = calculate_all_distances(coords2_aligned)
    max_dist_diff, mean_dist_diff, large_dist_diffs = compare_distance_matrices(
        dist1, dist2_aligned, args.tolerance)
    
    print(f"\nAll pairwise distances analysis:")
    print(f"  Maximum distance difference: {max_dist_diff:.4f} Å")
    print(f"  Mean distance difference: {mean_dist_diff:.4f} Å")
    
    print(f"\n{'='*50}")
    print("COMPARISON SUMMARY:")
    print(f"{'='*50}")
    
    if enantiomer_analysis['is_enantiomer']:
        print("🔄 Structures are ENANTIOMERS (mirror images)")
        print("   - Same connectivity and bond lengths")
        print("   - Opposite chirality/handedness")
    elif rmsd_after < 0.001:
        print("✓ Structures are essentially identical")
    elif rmsd_after < 0.01:
        print("✓ Structures are very similar")
    elif rmsd_after < 0.1:
        print("~ Structures are moderately similar")
    else:
        print("✗ Structures show significant differences")
    
    print(f"Final RMSD (all atoms): {rmsd_after:.4f} Å")
    print(f"Heavy-atom RMSD: {heavy_rmsd:.4f} Å")
    
    if args.verbose:
        output_file = f"aligned_{Path(args.file2).stem}.xyz"
        with open(output_file, 'w') as f:
            f.write(f"{len(symbols2)}\n")
            f.write(f"Aligned structure from {args.file2}\n")
            for symbol, coord in zip(symbols2, coords2_aligned):
                f.write(f"{symbol:2s} {coord[0]:12.6f} {coord[1]:12.6f} {coord[2]:12.6f}\n")
        print(f"\nAligned structure saved to: {output_file}")
    print()

if __name__ == "__main__":
    main()
