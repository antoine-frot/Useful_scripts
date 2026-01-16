#!/usr/bin/env python3
"""
Visualize Bader clusters in VESTA by assigning colors based on cluster analysis.

Reads Bader_summary.txt for cluster assignments and updates a vesta file
with cluster-specific colors either manually or automatically using Oklab.
"""

import os
import sys
import re
import argparse

from python_utility.oklab import generate_variants, hex_to_rgb

def parse_vesta_cluster_colors(filepath="VESTA_cluster_colors"):
    """
    Parse VESTA_element_colors to extract initial RGB colors per cluster.

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

def parse_bader_summary(filepath="Bader_summary.txt"):
    """
    Parse Bader_summary.txt to extract cluster assignments.
    
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
                    old_idx = int(parts[0].strip()) - 1  # Convert to 0-based
                    cluster_label = parts[2].strip()
                    cluster_map[old_idx] = cluster_label
            
    for cluster_label in cluster_map.values():
        if cluster_label not in cluster_counts:
            cluster_counts[cluster_label] = 0
        cluster_counts[cluster_label] += 1

    return cluster_map, cluster_counts


def parse_vesta_sitet(filepath="CONTCAR.vesta"):
    """
    Parse a .vesta file to extract SITET block and initial RGB colors per element.
    
    Returns:
        tuple: (vesta_lines, sitet_start_idx, sitet_end_idx, element_colors)
            - vesta_lines: all lines of the file
            - sitet_start_idx: line index where SITET data starts
            - sitet_end_idx: line index where SITET ends
            - element_colors: {element: (R, G, B)} from first occurrence
    """
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)
    
    with open(filepath, 'r') as f:
        vesta_lines = f.readlines()
    
    element_colors = {}
    sitet_start_idx = None
    sitet_end_idx = None
    
    for i, line in enumerate(vesta_lines):
        if line.strip() == "SITET":
            sitet_start_idx = i + 1
        elif sitet_start_idx is not None and sitet_end_idx is None:
            if line.strip() == "0 0 0 0 0 0":
                sitet_end_idx = i
                break
            # Parse SITET line
            parts = line.split()
            if len(parts) >= 6:
                # Extract element name (remove numbers from label like "Li1" -> "Li")
                label = parts[1]
                element = re.sub(r'\d+', '', label)
                
                # Extract RGB (columns 4, 5, 6 in 1-based = indices 3, 4, 5 in 0-based)
                try:
                    r = int(parts[3])
                    g = int(parts[4])
                    b = int(parts[5])
                    
                    # Store first occurrence only
                    if element not in element_colors:
                        element_colors[element] = (r, g, b)
                except (ValueError, IndexError):
                    continue
    
    if sitet_start_idx is None or sitet_end_idx is None:
        print(f"Error: Could not find SITET block in {filepath}.")
        sys.exit(1)
    
    return vesta_lines, sitet_start_idx, sitet_end_idx, element_colors


def get_manual_colors(cluster_map):
    """
    Prompt user to enter hex colors for each unique cluster.
    
    Returns:
        dict: {cluster_label: (R, G, B)}
    """
    unique_clusters = sorted(set(cluster_map.values()))
    cluster_colors = {}
    
    print("\n=== Manual Color Input ===")
    print("Enter hex color codes (e.g., #A8089E) for each cluster:\n")
    
    for cluster in unique_clusters:
        while True:
            color_input = input(f"{cluster}: ").strip()
            if not color_input.startswith('#'):
                color_input = '#' + color_input
            
            # Validate hex format
            if re.match(r'^#[0-9A-Fa-f]{6}$', color_input):
                rgb = hex_to_rgb(color_input)
                # Convert to 0-255 range
                cluster_colors[cluster] = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                break
            else:
                print("Invalid hex color. Please use format #RRGGBB")
    
    return cluster_colors


def get_automatic_colors(cluster_map, cluster_counts, element_colors: dict):
    """
    Generate colors automatically using Oklab color generation.
    Inputs:
        cluster_map: {old_idx (0-based): cluster_label}
        cluster_counts: {element: num_clusters}
        element_colors: {element: (R, G, B)}
    
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
        if elem not in elements_seen:
            elements_seen[elem] = 0
        if cluster not in cluster_seen:
            cluster_seen.add(cluster)
            elements_seen[elem] += 1
    
    for elem in elements_seen:
        r, g, b = element_colors[elem]
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        initial_hex_colors.append(hex_color)
        n_variants_per_color.append(elements_seen[elem])
        element_order.append(elem)

    print("\n=== Automatic Color Generation ===")
    print(f"Using Oklab to generate {sum(n_variants_per_color)} colors from {len(initial_hex_colors)} base colors")
    for elem, base, n_var in zip(element_order, initial_hex_colors, n_variants_per_color):
        print(f"  {elem}: {base} → {n_var} variant(s)")
    
    # Generate color palettes
    palette = generate_variants(initial_hex_colors, n_variants_per_color)
    
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


def update_vesta_colors(vesta_lines, sitet_start_idx, sitet_end_idx, cluster_map, cluster_colors):
    """
    Update SITET block RGB values based on cluster assignments.
    Inputs:
        vesta_lines: list of all lines in the .vesta file
        sitet_start_idx: line index where SITET data starts
        sitet_end_idx: line index where SITET data ends
        cluster_map: {old_idx (0-based): cluster_label}
        cluster_colors: {cluster_label: (R, G, B)}
    
    Returns:
        list: Updated vesta_lines
    """
    updated_lines = vesta_lines.copy()
    
    for sitet_idx in range(sitet_start_idx, sitet_end_idx):
        atom_idx = sitet_idx - sitet_start_idx  # 0-based atom index
        
        if atom_idx in cluster_map:
            cluster = cluster_map[atom_idx]
            if cluster in cluster_colors:
                r, g, b = cluster_colors[cluster]
                
                # Parse and update the line
                parts = updated_lines[sitet_idx].split()
                if len(parts) >= 6:
                    parts[3] = str(r)
                    parts[4] = str(g)
                    parts[5] = str(b)
                    parts[6] = str(r)
                    parts[7] = str(g)
                    parts[8] = str(b)
                    # Reconstruct line preserving formatting
                    # Use fixed-width formatting to match VESTA style
                    # First color is the atom color (columns 4,5,6) and the second color is polyhedra color (columns 7,8,9). They should be the same
                    updated_lines[sitet_idx] = f"{parts[0]:>3} {parts[1]:>10} {parts[2]:>7} {parts[3]:>3} {parts[4]:>3} {parts[5]:>3} {parts[6]:>3} {parts[7]:>3} {parts[8]:>3}"
                    if len(parts) > 9:
                        updated_lines[sitet_idx] += " " + " ".join(parts[9:])
                    updated_lines[sitet_idx] += "\n"
    
    return updated_lines


def main():
    """Main execution function."""
    if args.verbose:
        print("=" * 60)
        print("VESTA Cluster Visualization Tool")
        print("=" * 60)
        
    # Step 1: Parse Bader summary
        print("\n[1/4] Parsing Bader_summary.txt...")
    cluster_map, cluster_counts = parse_bader_summary()
    if args.verbose:
        number_of_elements = len(set([cluster.rstrip('0123456789') for cluster in cluster_map.values()]))
        print(f"  Found {len(cluster_map)} atoms in {len(cluster_counts)} clusters and {number_of_elements} elements")

    # Step 2: Parse VESTA file
        print(f"\n[2/4] Parsing {args.vesta}...")
    vesta_lines, sitet_start, sitet_end, element_colors = parse_vesta_sitet(args.vesta)
    if args.verbose:
        print(f"  SITET block: lines {sitet_start+1} to {sitet_end}")
        if number_of_elements == len(element_colors):
            print(f"  Element base colors: {len(element_colors)} found")
        else:
            print(f"  Warning: {len(element_colors)} element colors found, but {number_of_elements} are expected")
    
    # Step 3: Get colors (manual or automatic)
        print("\n[3/4] Color assignment...")
    VESTA_cluster_colors_path = "VESTA_cluster_colors"
    if VESTA_cluster_colors_path in os.listdir('.'):
        print(f"Found {VESTA_cluster_colors_path} file. Using it for base colors.")
        cluster_colors = parse_vesta_cluster_colors(VESTA_cluster_colors_path)
        if len(cluster_colors) != len(cluster_counts):
            print(f"Warning: Number of clusters in {VESTA_cluster_colors_path} ({len(cluster_colors)}) "
                  f"does not match number of clusters found ({len(cluster_counts)}).")
            sys.exit(1)
    else:
        while True:
            mode = input("Choose color mode - (m)anual or (a)utomatic? [default: a]: ").strip().lower()
            if mode in ['', 'a', 'automatic']:
                cluster_colors = get_automatic_colors(cluster_map, cluster_counts, element_colors)
                break
            elif mode in ['m', 'manual']:
                cluster_colors = get_manual_colors(cluster_map)
                break
            else:
                print("Invalid choice. Please enter 'm' or 'a'.")

    if args.verbose:
        print(f"\nColor mapping created for {len(cluster_colors)} clusters")

    # Step 4: Update VESTA file
        print(f"\n[4/4] Updating {args.vesta}...")
    updated_lines = update_vesta_colors(vesta_lines, sitet_start, sitet_end, cluster_map, cluster_colors)
    
    with open(f"{args.vesta}", 'w') as f:
        f.writelines(updated_lines)
    
    if args.verbose:
        print("\n" + "=" * 60)
        print(f"SUCCESS: {args.vesta} updated with cluster colors")
        print("=" * 60)
        print("\nCluster color summary:")
        for cluster in sorted(cluster_colors.keys()):
            r, g, b = cluster_colors[cluster]
            print(f"  {cluster:6s}: RGB({r:3d}, {g:3d}, {b:3d})  #{r:02x}{g:02x}{b:02x}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VESTA Cluster Visualization Tool")
    parser.add_argument("--vesta", type=str, default="CONTCAR.vesta", help="Path to the output VESTA file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    main()