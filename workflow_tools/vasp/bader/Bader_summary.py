#! /home/afrot/virtual_env_python/bin/python3
import os
import math
"""
Write a summary of Bader charge and magnetization analysis from ACF_chg.dat and ACF_mag.dat files.
Generates a summary file 'Bader_summary.txt' with individual atom data and statistics per element.
Such as:
   #     Ion    Bader (e)     Charge     Mag (muB)
----------------------------------------------------
   1     Li1      0.15         0.85         0.00                                                                                                                                                                                            
   2     Li2      0.12         0.88         0.00
   3     Mn1      5.25         1.75         3.09
   4     Mn1      5.25         1.75         3.09
   5     O1       6.85        -0.85        -0.35
   6     O1       6.85        -0.85        -0.35
   7     O2       6.88        -0.88        -0.37
   8     O2       6.88        -0.88        -0.37
   9     O2       6.88        -0.88        -0.37
  10     O2       6.88        -0.88        -0.37
----------------------------------------------------
TOTAL ELECTRONS:     52.00
TOTAL MAGNETIZATION: 4.00


Element   Min(Bader)   Max(Bader)  RMSD(Bader)    Min(Mag)     Max(Mag)    RMSD(Mag)
--------------------------------------------------------------------------------------
Li           0.12         0.15         0.01         0.00         0.00         0.00
Mn           5.25         5.25         0.00         3.09         3.09         0.00
O            6.85         6.88         0.01        -0.37        -0.35         0.01
"""

# ================= CONFIGURATION =================
OUTPUT_FILE = "Bader_summary.txt"
# TOLERANCE = 0.04  # Difference required to classify as a distinct ion
# =================================================

def get_geometry_info():
    """Reads POSCAR/CONTCAR to get element names and counts."""
    geo_file = "POSCAR"
    if os.path.exists("CONTCAR") and os.path.getsize("CONTCAR") > 0:
        geo_file = "CONTCAR"
    
    if not os.path.exists(geo_file):
        print(f"Error: Could not find POSCAR or CONTCAR.")
        return None, None

    try:
        with open(geo_file, 'r') as f:
            lines = f.readlines()
            elems = lines[5].split()
            counts = [int(x) for x in lines[6].split()]
            
            if elems[0].isdigit():
                print("Error: VASP 4 POSCAR format detected (no element symbols).")
                return None, None
            
            atom_names = []
            for e, c in zip(elems, counts):
                atom_names.extend([e] * c)
            return atom_names, dict(zip(elems, [0.0]*len(elems)))
    except Exception as e:
        print(f"Error parsing geometry: {e}")
        return None, None

def get_zvals(elements_dict):
    """Reads POTCAR to get ZVALs for net charge calculation."""
    if not os.path.exists("POTCAR"):
        print("Warning: POTCAR not found. Net Charge will be incorrect.")
        return elements_dict
    
    try:
        current_elem_idx = 0
        ordered_elems = list(elements_dict.keys())
        
        with open("POTCAR", 'r') as f:
            for line in f:
                if "ZVAL" in line:
                    parts = line.split(";")
                    for p in parts:
                        if "ZVAL" in p:
                            val = float(p.split("=")[1].split()[0])
                            if current_elem_idx < len(ordered_elems):
                                elements_dict[ordered_elems[current_elem_idx]] = val
                                current_elem_idx += 1
    except Exception as e:
        print(f"Error parsing POTCAR: {e}")
    
    return elements_dict

def read_acf(filename):
    """Reads the Charge or Mag file."""
    values = []
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return []
    
    try:
        with open(filename, 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 6 and parts[0].isdigit():
                    values.append(float(parts[4]))
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return values

def generate_ion_labels(atoms, charges, mags, tolerance=6e-2):
    """Generates labels using DBSCAN clustering."""
    from sklearn.cluster import DBSCAN
    from collections import defaultdict
    import numpy as np
    
    labels = [''] * len(atoms)
    element_groups = defaultdict(list)
    
    # Group by element
    for i, elem in enumerate(atoms):
        element_groups[elem].append(i)
    
    # Cluster each element separately
    for elem, indices in element_groups.items():
        features = np.array([[charges[i], mags[i]] for i in indices])
        
        # DBSCAN clustering
        clustering = DBSCAN(eps=tolerance, min_samples=1).fit(features)
        
        # Sort clusters by centroid for consistency
        unique_clusters = sorted(set(clustering.labels_))
        cluster_mapping = {}
        for new_id, old_id in enumerate(unique_clusters, 1):
            cluster_mapping[old_id] = new_id
        
        # Assign labels
        for i, cluster_id in enumerate(clustering.labels_):
            labels[indices[i]] = f"{elem}{cluster_mapping[cluster_id]}"
    
    return labels

def calculate_stats(data_list):
    """Returns Min, Max, and RMSD."""
    if not data_list:
        return 0.0, 0.0, 0.0
    
    mini = min(data_list)
    maxi = max(data_list)
    mean = sum(data_list) / len(data_list)
    variance = sum([((x - mean) ** 2) for x in data_list]) / len(data_list)
    rmsd = math.sqrt(variance)
    
    return mini, maxi, rmsd

# ================= MAIN LOGIC =================

def main():
    atoms, zval_map = get_geometry_info()
    if not atoms: return
    
    zval_map = get_zvals(zval_map)
    bader_vals = read_acf("ACF_chg.dat")
    mag_vals = read_acf("ACF_mag.dat")
    
    if len(bader_vals) != len(atoms) or len(mag_vals) != len(atoms):
        print(f"Error: Mismatch in atom counts.")
        return

    net_charges = []
    for i, atom in enumerate(atoms):
        z = zval_map.get(atom, 0.0)
        net_charges.append(z - bader_vals[i])

    ion_labels = generate_ion_labels(atoms, bader_vals, mag_vals)

    # Create a list of tuples: (original_index, element, label, bader, charge, mag)
    atom_data = []
    total_elec = 0.0
    total_mag = 0.0
    for i in range(len(atoms)):
        atom_data.append((i+1, atoms[i], ion_labels[i], bader_vals[i], net_charges[i], mag_vals[i]))
        total_elec += bader_vals[i]
        total_mag += mag_vals[i]

    # Sort by: (1) first appearance of element, (2) cluster index, (3) Bader charge
    unique_elements_order = []
    for elem in atoms:
        if elem not in unique_elements_order:
            unique_elements_order.append(elem)

    def sort_key(x):
        elem = x[1]
        label = x[2]
        bader_charge = x[3]
        elem_order = unique_elements_order.index(elem)
        
        # Extract cluster index from label (e.g., 'Fe1' -> 1)
        cluster_index_str = ''.join(filter(str.isdigit, label))
        cluster_index = int(cluster_index_str) if cluster_index_str else 0
        
        return (elem_order, cluster_index, bader_charge)

    atom_data.sort(key=sort_key)

    with open(OUTPUT_FILE, 'w') as f:
        # --- TABLE 1: Individual Atoms ---
        # UPDATED: Using >12 for right alignment to fix formatting shift
        header = f"{'#':>4}     {'Ion':<4}  {'Bader (e)':^12}{'Charge':^12} {'Mag (muB)':^12}"
        
        f.write("Individual Atom Data:\n")
        f.write("-" * len(header) + "\n")
        f.write(header + "\n")
        f.write("-" * len(header) + "\n")
        
        for orig_idx, elem, label, bader, charge, mag in atom_data:
            f.write(f"{orig_idx:>4}     {label:<4} {bader:^12.2f} {charge:^12.2f} {mag:^12.2f}\n")
            
        f.write("-" * len(header) + "\n")
        # Get the length of a floating point number for alignment
        displayed_total_mag = f"{total_mag:.2f}"
        f.write(f"TOTAL ELECTRONS: {total_elec:>{len(displayed_total_mag)+4}.2f}\n")
        f.write(f"TOTAL MAGNETIZATION: {displayed_total_mag}\n")
        f.write("\n\n")

        # --- TABLE 2: Statistics per Element ---
        # UPDATED: Using right alignment here too
        f.write("Element-wise Statistics:\n")
        stats_header = (f"{'Element':<8} "
                        f"{'Min(Bader)':^12} {'Max(Bader)':^12} {'RMSD(Bader)':^12} "
                        f"{'Min(Mag)':^12} {'Max(Mag)':^12} {'RMSD(Mag)':^12}")
        f.write("-" * len(stats_header) + "\n")
        f.write(stats_header + "\n")
        f.write("-" * len(stats_header) + "\n")

        unique_elements = sorted(list(set(atoms)), key=lambda x: atoms.index(x))
        
        for elem in unique_elements:
            e_bader = [bader_vals[i] for i, a in enumerate(atoms) if a == elem]
            e_mag   = [mag_vals[i]   for i, a in enumerate(atoms) if a == elem]
            
            min_b, max_b, rms_b = calculate_stats(e_bader)
            min_m, max_m, rms_m = calculate_stats(e_mag)
            
            f.write(f"{elem:<8} "
                    f"{min_b:^12.2f} {max_b:^12.2f} {rms_b:^12.2f} "
                    f"{min_m:^12.2f} {max_m:^12.2f} {rms_m:^12.2f}\n")
        f.write("-" * len(stats_header) + "\n")

    print(f"Analysis complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()