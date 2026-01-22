#!/usr/bin/env python3
"""
Visualize Bader clusters in VESTA by assigning colors based on cluster analysis.

Reads Bader_summary.txt (allowing for changes in cluster definitions) for cluster assignments and updates a vesta file
with cluster-specific colors either manually or automatically using Oklab.
"""

import os
import sys
import re
import argparse

from python_utility.oklab import generate_variants, hex_to_rgb
from python_utility.vesta_colors import vesta_colors

def parse_vesta_cluster_colors(filepath="VESTA_cluster_colors"):
    """
    Parse VESTA_element_colors to extract initial HEX colors per cluster.

    Returns:
        dict: {cluster: (R, G, B)}
    File example:
    Li1: #86df73
    Mn1: #74006d
    Mn2: #d950cc
    O1: #fe604c
    O2: #c20000
    """
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)
    
    cluster_colors = {}
    
    with open(filepath, 'r') as f:
        for line in f:
            if ':' in line:
                cluster, hex_color = line.split(':', 1)
                cluster = cluster.strip()
                hex_color = hex_color.strip()
                rgb = hex_to_rgb(hex_color)
                cluster_colors[cluster] = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

    return cluster_colors

def write_vesta_cluster_colors(cluster_colors, filepath="VESTA_cluster_colors"):
    """
    Write cluster colors to VESTA_cluster_colors file.
    
    Inputs:
        cluster_colors: {cluster: (R, G, B)}
    """
    with open(filepath, 'w') as f:
        for cluster in sorted(cluster_colors.keys()):
            r, g, b = cluster_colors[cluster]
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            f.write(f"{cluster}: {hex_color}\n")

def parse_bader_summary(index='old', filepath="Bader_summary.txt"):
    """
    Parse Bader_summary.txt to extract cluster assignments.

    Inputs:
        index: 'old' or 'new' to specify which atom indexing to use. 'old' uses original atom indices from CONTCAR, 'new' uses reordered indices.
        filepath: path to Bader_summary.txt file
    
    Returns:
        tuple: (cluster_map, cluster_counts)
            - cluster_map: {old_idx (0-based): cluster_label}
            - cluster_counts: {element: num_clusters}
    """
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)
    
    cluster_map = {}
    cluster_counts = {}
    if index not in ['old', 'new']:
        print(f"Error: index must be 'old' or 'new'.")
        sys.exit(1)
    if index == 'new':
        idx_col = 1  # New index column
    else:
        idx_col = 0  # Old index column

    with open(filepath, 'r') as f:
        in_data_section = False
        
        for line in f:
            # Parse Individual Atom Data section
            if "Individual Atom Data:" in line:
                in_data_section = True
                continue
            elif in_data_section and line.strip().startswith("TOTAL"):
                in_data_section = False
                continue
            elif in_data_section:
                if line.strip().startswith('-') or '#(old)' in line or not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 3 and parts[0].strip().isdigit():
                    old_idx = int(parts[idx_col].strip()) - 1  # Convert to 0-based
                    cluster_label = parts[2].strip()
                    cluster_map[old_idx] = cluster_label
            
    for cluster_label in cluster_map.values():
        if cluster_label not in cluster_counts:
            cluster_counts[cluster_label] = 0
        cluster_counts[cluster_label] += 1

    return cluster_map, cluster_counts

def get_automatic_colors(cluster_map):
    """
    Generate colors automatically using Oklab color generation.
    Inputs:
        cluster_map: {old_idx (0-based): cluster_label}
        cluster_counts: {element: num_clusters}
    
    Returns:
        dict: {cluster_label: (R, G, B)}
    """
    # Prepare data for generate_variants
    initial_hex_colors = []
    n_variants_per_color = []
    element_order = []
    
    # Sort elements by appearance in cluster_map
    elements_seen = {}
    cluster_seen = set()
    for cluster in cluster_map.values():
        elem = re.sub(r'\d+', '', cluster)
        # Skip if target_elements specified and this element not in it
        if elem not in elements_seen:
            elements_seen[elem] = 0
        if cluster not in cluster_seen:
            cluster_seen.add(cluster)
            elements_seen[elem] += 1
    
    for elem in elements_seen:
        hex_color = vesta_colors[elem]
        initial_hex_colors.append(hex_color)
        n_variants_per_color.append(elements_seen[elem])
        element_order.append(elem)

    if args.verbose:
        print("\n=== Automatic Color Generation ===")
        print(f"Using Oklab to generate {sum(n_variants_per_color)} colors from {len(initial_hex_colors)} base colors")
        for elem, base, n_var in zip(element_order, initial_hex_colors, n_variants_per_color):
            print(f"  {elem}: {base} → {n_var} variant(s)")
    
    # Generate color palettes
    palette = generate_variants(initial_hex_colors, n_variants_per_color, spread=0.3, luminescence_max=0.8)
    
    # Map cluster labels to colors
    cluster_colors = {}
    for elem, hex_base in zip(element_order, initial_hex_colors):
        variants = palette[hex_base]
        # Get all clusters for this element, sorted by cluster number
        elem_clusters = sorted(
            [c for c in set(cluster_map.values()) if c.startswith(elem)],
            key=lambda x: int(re.search(r'\d+', x).group())
        )
        
        for cluster, hex_color in zip(elem_clusters, variants):
            rgb = hex_to_rgb(hex_color)
            cluster_colors[cluster] = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
    
    return cluster_colors

def update_vesta_colors(filepath, cluster_map, cluster_colors, VESTA_cluster_colors_path="VESTA_cluster_colors"):
    """
    Update SITET block RGB values in a VESTA file based on cluster assignments.
    
    Inputs:
        filepath: path to the VESTA file
        cluster_map: {old_idx (0-based): cluster_label}
        cluster_colors: {cluster_label: (R, G, B)}
    """
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)
    
    # Read the file
    with open(filepath, 'r') as f:
        vesta_lines = f.readlines()
    
    # Find SITET block
    sitet_start_idx = None
    sitet_end_idx = None
    
    for i, line in enumerate(vesta_lines):
        if line.strip() == "SITET":
            sitet_start_idx = i + 1
        elif sitet_start_idx is not None and sitet_end_idx is None:
            if line.strip() == "0 0 0 0 0 0": # End of SITET block
                sitet_end_idx = i
                break
    
    if sitet_start_idx is None or sitet_end_idx is None:
        print(f"Error: Could not find SITET block in {filepath}.")
        sys.exit(1)
    
    # Update colors for ALL atoms
    for sitet_idx in range(sitet_start_idx, sitet_end_idx):
        atom_idx = sitet_idx - sitet_start_idx  # 0-based atom index
        
        # Parse the line to get element
        parts = vesta_lines[sitet_idx].split()
        if len(parts) < 6:
            continue
            
        label = parts[1]
        element = re.sub(r'\d+', '', label)
        
        # Determine which color to use
        if args.element is None or element in args.element:
            cluster = cluster_map[atom_idx]
            if cluster not in cluster_colors:
                print(f"Error: No color found for cluster {cluster}. Please check {VESTA_cluster_colors_path}.")
                sys.exit(1)
            r, g, b = cluster_colors[cluster]
        else:
            hex_color = vesta_colors[element]
            rgb = hex_to_rgb(hex_color)
            r, g, b = int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)

        # Apply the color
        parts[3] = str(r)
        parts[4] = str(g)
        parts[5] = str(b)
        parts[6] = str(r)
        parts[7] = str(g)
        parts[8] = str(b)
        
        # Reconstruct line preserving formatting
        vesta_lines[sitet_idx] = f"{parts[0]:>3} {parts[1]:>10} {parts[2]:>7} {parts[3]:>3} {parts[4]:>3} {parts[5]:>3} {parts[6]:>3} {parts[7]:>3} {parts[8]:>3}"
        if len(parts) > 9:
            vesta_lines[sitet_idx] += " " + " ".join(parts[9:])
        vesta_lines[sitet_idx] += "\n"
    
    # Write the updated file
    with open(filepath, 'w') as f:
        f.writelines(vesta_lines)


def main():
    """Main execution function."""
    if args.verbose:
        print("=" * 60)
        print("VESTA Cluster Visualization Tool")
        print("=" * 60)
        
    # Step 1: Parse Bader summary
    if args.verbose:
        print("\n[1/3] Parsing Bader_summary.txt...")
    if args.input == "CONTCAR_ordered.vesta":
        cluster_map, cluster_counts = parse_bader_summary(index='new')
    else:
        cluster_map, cluster_counts = parse_bader_summary(index='old')

    if args.verbose:
        number_of_elements = len(set([cluster.rstrip('0123456789') for cluster in cluster_map.values()]))
        print(f"  Found {len(cluster_map)} atoms in {len(cluster_counts)} clusters and {number_of_elements} elements")
    
    # Step 2: Get colors
    if args.verbose:
        print("\n[2/3] Color assignment...")
    VESTA_cluster_colors_path = "VESTA_cluster_colors"
    if VESTA_cluster_colors_path in os.listdir('.'):
        print(f"Found {VESTA_cluster_colors_path} file. Using it for base colors.")
        cluster_colors = parse_vesta_cluster_colors(VESTA_cluster_colors_path)
    else:
        print(f"No {VESTA_cluster_colors_path} file found. Generating colors automatically using Oklab.")
        cluster_colors = get_automatic_colors(cluster_map)
        write_vesta_cluster_colors(cluster_colors, VESTA_cluster_colors_path)

    if args.verbose:
        print(f"\nColor mapping created for {len(cluster_colors)} clusters")
    
    # Step 3: Update VESTA file
    if args.verbose:
        print(f"\n[3/3] Updating {args.input}...")
    update_vesta_colors(args.input, cluster_map, cluster_colors, VESTA_cluster_colors_path)
    
    if args.verbose:
        print("\n" + "=" * 60)
        print(f"SUCCESS: {args.input} updated with cluster colors")
        print("=" * 60)
        print("\nCluster color summary:")
        for cluster in sorted(cluster_colors.keys()):
            r, g, b = cluster_colors[cluster]
            print(f"  {cluster:6s}: RGB({r:3d}, {g:3d}, {b:3d})  #{r:02x}{g:02x}{b:02x}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VESTA Cluster Visualization Tool. Assign colors to atoms based on Bader cluster analysis. Colors are generated automatically using Oklab unless a VESTA_cluster_colors file is provided.")
    parser.add_argument("-i", "--input", type=str, default="CONTCAR.vesta", help="Path to the input VESTA file (default: CONTCAR.vesta)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-e", "--element", type=str, nargs='+', help="Element(s) to apply cluster colors to (e.g., Mn O). If not specified, all elements are colored.")
    args = parser.parse_args()
    if args.verbose:
        print(f"Input VESTA file: {args.input}")
        if args.element:
            print(f"Target elements for coloring: {', '.join(args.element)}")
        else:
            print("All elements will be colored based on clusters.")
    if not args.input.endswith('.vesta'):
        print("Error: Input file must be a .vesta file.")
        sys.exit(1)
    if args.input not in os.listdir('.'):
        print(f"Error: {args.input} not found in the current directory.")
        sys.exit(1)
    main()