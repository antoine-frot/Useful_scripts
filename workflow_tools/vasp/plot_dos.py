#! /home/afrot/virtual_env_python/bin/python3
import matplotlib.pyplot as plt
import warnings
import argparse
import os

def read_mn_oxidation_states():
    """Read Mn oxidation state assignments from Bader_summary.txt file.
    
    Reads the cluster information where:
    - First Mn cluster (Mn1) = Mn(IV)
    - Second Mn cluster (Mn2) = Mn(III)
    
    Returns dict with 0-indexed atom positions:
    {
        "Mn(IV)": [0, 1, 2],
        "Mn(III)": [3, 4, 5]
    }
    """
    bader_file = "Bader_summary.txt"
    if not os.path.exists(bader_file):
        return None
    
    try:
        mn_clusters = {}
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
                    
                    # Check if this is a Mn atom
                    if ion_label.startswith('Mn') and old_idx.isdigit():
                        if ion_label not in mn_clusters:
                            mn_clusters[ion_label] = []
                        # Convert to 0-indexed
                        mn_clusters[ion_label].append(int(old_idx) - 1)
        
        # Map cluster labels to oxidation states
        # Sort cluster labels to ensure consistent ordering (Mn1, Mn2, etc.)
        sorted_clusters = sorted(mn_clusters.keys(), key=lambda x: int(x.replace('Mn', '')))
        
        if len(sorted_clusters) == 0:
            return None
        
        oxidation_states = {}
        # First cluster = Mn(IV), second = Mn(III)
        oxidation_states["Mn(IV)"] = mn_clusters[sorted_clusters[0]]
        if len(sorted_clusters) >= 2:
            oxidation_states["Mn(III)"] = mn_clusters[sorted_clusters[1]]
        
        return oxidation_states if oxidation_states else None
        
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
    
    if args.mn_oxidation:
        mn_config = read_mn_oxidation_states()
    
    if mn_config:
        # Get element DOS but exclude Mn (we'll handle it separately)
        element_dos_dict = dos.get_element_dos()
        for element, element_dos in element_dos_dict.items():
            if element.symbol != 'Mn':
                plotter.add_dos(str(element), element_dos)
        
        # Add separate DOS for each Mn oxidation state
        structure = vasprun.final_structure
        for label, indices in mn_config.items():
            # Sum DOS over all atoms in this oxidation state
            mn_dos = None
            for idx in indices:
                site_dos = dos.get_site_dos(structure[idx])
                if mn_dos is None:
                    mn_dos = site_dos
                else:
                    # Sum the DOS
                    for spin in site_dos.densities:
                        mn_dos.densities[spin] += site_dos.densities[spin]
            
            if mn_dos:
                plotter.add_dos(label, mn_dos)
    else:
        # Original behavior: plot element DOS
        plotter.add_dos_dict(dos.get_element_dos())
    
    ax = plotter.get_plot()  # Get Axis object
    lines = ax.get_lines()
    
    # Define colors for Mn oxidation states
    mn_colors = {
        'Mn3+': '#8B4513',  # Saddle brown
        'Mn4+': '#4B0082',  # Indigo
        'Mn(III)': '#8B4513',
        'Mn(IV)': '#4B0082'
    }
    
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
        elif label in mn_colors:
            line.set_color(mn_colors[label])
        elif label == 'Total DOS':
            if args.total:
                line.set_color('#000000')  # Black for total DOS
            else:
                line.remove()  # Remove total DOS line if not requested
        line.set_linewidth(1)
    # Remove extra white space
    ax.margins(0)
    ax.autoscale_view()
    # Remove duplicate labels in legend for spin polarized DOS
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), fontsize='x-large')
    save_to_agr(ax, "dos.agr")
    fig = plt.gcf()        # Get current figure
    plt.tight_layout()  # Adjust layout to prevent clipping
    plt.savefig("dos_full.png", dpi=600)  # Save figure
    plt.savefig("dos_full.pdf")  # Save figure
    from python_utility.matplotlib.enable_interactive_plot import enable_scroll_zoom, enable_keyboard_pan
    enable_scroll_zoom(fig)
    enable_keyboard_pan(fig)
    plt.show()               # Display

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot DOS from VASP vasprun.xml")
    parser.add_argument('-t', '--total', action='store_true', help='Add total DOS to the plot')
    parser.add_argument('-m', '--mn-oxidation', action='store_true', help='Plot a line for each Mn oxidation states (only Mn(III) and Mn(IV) implemented)')
    args = parser.parse_args()
    main()