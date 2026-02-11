#!/usr/bin/env python3
import matplotlib.pyplot as plt
import warnings
import argparse
import os
import shutil
import sys
from workflow_tools.vasp.visualize_cluster import parse_vesta_cluster_colors

def read_oxidation_states(element_symbol):
    """Read oxidation state assignments from Bader_summary.txt file.
    
    Returns dict with 0-indexed atom positions:
    {
        "ElementCluster1": [0, 1, 4],
        "ElementCluster2": [2, 3, 5]
    }
    """
    bader_file = "Bader_summary.txt"
    if not os.path.exists(bader_file):
        return None
    
    try:
        clusters = {}
        with open(bader_file, 'r') as f:
            in_atom_data = False
            for line in f:
                # Start reading after header
                if "Individual Atom Data:" in line:
                    in_atom_data = True
                    continue
                
                # Stop at the separator after data
                if in_atom_data and line.startswith("TOTAL"):
                    break
                
                # Skip header and separator lines
                if not in_atom_data or line.startswith('-') or '#(old)' in line:
                    continue
                
                parts = line.split()
                if len(parts) >= 3:
                    old_idx = parts[0].strip()
                    ion_label = parts[2].strip()
                    
                    # Check if this is a specific element atom
                    if ion_label.startswith(element_symbol) and old_idx.isdigit():
                        if ion_label not in clusters:
                            clusters[ion_label] = []
                        # Convert to 0-indexed
                        clusters[ion_label].append(int(old_idx) - 1)

        return clusters
        
    except Exception as e:
        print(f"Error reading Bader summary: {e}")
        return None

def main():
    # Filter out the specific networkx warning occuring on taz
    warnings.filterwarnings("ignore", message="networkx backend defined more than once: nx-loopback")
    from pymatgen.io.vasp.outputs import Vasprun
    from pymatgen.electronic_structure.plotter import DosPlotter
    from pymatgen.electronic_structure.core import Spin
    from python_utility.vesta_colors import vesta_colors
    from python_utility.matplotlib.save_to_agr import save_to_agr
    vasprun = Vasprun("vasprun.xml", parse_projected_eigen=True)
    dos = vasprun.complete_dos # Total DOS + projection on atoms and orbitals

    plotter = DosPlotter()
    plotter.add_dos('Total DOS', dos)
    
    # Determine which elements to show
    target_elements = []
    if args.element:
        target_elements = [e.capitalize() for e in args.element]
    
    # Ensure cluster elements are included in target_elements
    cluster_elements = []
    if args.cluster:
        cluster_elements = [e.capitalize() for e in args.cluster]
        for element in cluster_elements:
            if element not in target_elements:
                target_elements.append(element)
    
    clusters = {}
    if args.cluster:
        # Normalize element names to capitalized format
        for element in cluster_elements:
            clusters[element] = read_oxidation_states(element)
    
    if clusters:
        # Get element DOS but exclude element clusters (will be handled separately)
        cluster_colors = parse_vesta_cluster_colors()
        element_dos_dict = dos.get_element_dos()
        for element, element_dos in element_dos_dict.items():
            # Skip if not in target_elements (when element filter is active)
            if target_elements and element.symbol not in target_elements:
                continue
            # Skip cluster elements as they will be handled separately
            if element.symbol not in cluster_elements:
                plotter.add_dos(str(element), element_dos)
        
        # Add separate DOS for each element cluster
        structure = vasprun.final_structure
        for element in cluster_elements:
            if element not in clusters or clusters[element] is None:
                continue
            for label, indices in clusters[element].items():
                dos_cluster = None
                for idx in indices:
                    site_dos = dos.get_site_dos(structure[idx])
                    if dos_cluster is None:
                        dos_cluster = site_dos
                    else:
                        # Sum the DOS
                        for spin in site_dos.densities:
                            dos_cluster.densities[spin] += site_dos.densities[spin]

                if dos_cluster:
                    plotter.add_dos(label, dos_cluster)
    else:
        # Original behavior: plot element DOS
        element_dos_dict = dos.get_element_dos()
        if target_elements:
            # Filter by specified elements
            filtered_dos = {element: element_dos for element, element_dos in element_dos_dict.items() 
                          if element.symbol in target_elements}
            plotter.add_dos_dict(filtered_dos)
        else:
            # Show all elements
            plotter.add_dos_dict(element_dos_dict)
    
    ax = plotter.get_plot()
    lines = ax.get_lines()
    # Customize colors and line widths
    for line in lines:
        label = line.get_label()
        if label.startswith('_'):
            y_values = line.get_ydata()
            
            # We use a small epsilon (1e-5) to handle potential floating point errors.
            if all(abs(y) < 1e-5 for y in y_values):
                line.remove()  # Deletes the line from the plot
            else:
                line.set_color('black')
                line.set_linestyle('--')
                line.set_linewidth(0.5)
                
            continue
        if label in vesta_colors:
            line.set_color(vesta_colors[label])
        elif clusters and label in cluster_colors:
            r, g, b = cluster_colors[label]
            line.set_color((r/255, g/255, b/255))
            if label == 'Mn1':
                label = 'Mn(IV)'
            if label == 'Mn2':
                label = 'Mn(III)'
            if label == 'Mn3':
                label = 'Mn(II)'
                ydata = line.get_ydata()
                line.set_ydata(ydata * 8)
            # if label == 'O1':
            #    label = 'O_eq'
            # if label == 'O2':
            #    label = 'O_JT'
            line.set_label(f"{label}")

            
        elif label == 'Total DOS':
            if args.total:
                line.set_color('#000000')  # Black for total DOS
            else:
                line.remove()  # Remove total DOS line if not requested
        line.set_linewidth(1)
    # Add horizontal line at y=0
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.8)
    # Remove extra white space
    ax.margins(0)
    ax.autoscale_view()
    # Remove duplicate labels in legend for spin polarized DOS
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), fontsize=20)
    xfontsize = ax.xaxis.get_label().get_fontsize()
    yfontsize = ax.yaxis.get_label().get_fontsize()
    ax.set_xlabel("Energy (eV)", fontsize=xfontsize)
    ax.set_ylabel("Density of States (arb. unit)", fontsize=yfontsize)
    # ax.set_xlim(-8, 4.5)
    
    # Build output filename suffix based on flags
    suffix = ""
    if args.element:
        suffix += "_elem_" + "_".join(args.element)
    if args.cluster:
        suffix += "_clust_" + "_".join(args.cluster)
    
    save_to_agr(ax, f"dos{suffix}.agr")
    fig = plt.gcf()        # Get current figure
    plt.tight_layout()  # Adjust layout to prevent clipping
    plt.savefig(f"dos_full{suffix}.png", dpi=600)  # Save figure
    plt.savefig(f"dos_full{suffix}.pdf")  # Save figure
    from python_utility.matplotlib.enable_interactive_plot import enable_scroll_zoom, enable_keyboard_pan
    enable_scroll_zoom(fig)
    enable_keyboard_pan(fig)
    plt.show()               # Display

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot DOS from VASP vasprun.xml")
    parser.add_argument('-t', '--total', action='store_true', help='Add total DOS to the plot')
    parser.add_argument("-e", "--element", type=str, nargs='+', help="Element(s) to show DOS for (e.g., Mn O). If not specified, all elements are shown. Elements in --cluster are automatically included.")
    parser.add_argument("-c", "--cluster", type=str, nargs='+', help="Element(s) to differentiate clusters for (e.g., Mn O). If not specified, element-projected DOS is shown without cluster differentiation.")
    args = parser.parse_args()
    # Copy script to current directory as dos_plotter.py
    if "dos_plotter.py" not in os.listdir("."):
        shutil.copy(__file__, "dos_plotter.py")
    else:
        # check if the file is identical to the current script
        with open(__file__, 'r') as f1, open("dos_plotter.py", 'r') as f2:
            if not f1.read() == f2.read():
                print("dos_plotter.py exists in this directory and is different.")
                response = input("Do you want to run dos_plotter.py instead? (y/n): ")
                if response.lower() == 'y':
                    # Add the same arguments
                    os.system("python3 dos_plotter.py " + " ".join(sys.argv[1:]))
                    exit(0)
    main()