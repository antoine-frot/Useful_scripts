#! /home/afrot/virtual_env_python/bin/python3
import matplotlib.pyplot as plt
import warnings
import sys
import os
import numpy as np
# Filter out the specific networkx warning occuring on taz
warnings.filterwarnings("ignore", message="networkx backend defined more than once: nx-loopback")
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.plotter import DosPlotter
from python_utility.vesta_colors import vesta_colors

def load_dos(directory):
    """Load DOS from a vasprun.xml file in the given directory."""
    vasprun_path = os.path.join(directory, "vasprun.xml")
    if not os.path.exists(vasprun_path):
        raise FileNotFoundError(f"vasprun.xml not found in {directory}")
    vasprun = Vasprun(vasprun_path, parse_projected_eigen=True)
    return vasprun.complete_dos

def compute_dos_difference(dos1, dos2):
    """Compute the difference between two DOS objects (dos1 - dos2)."""
    from pymatgen.electronic_structure.core import Spin
    
    # Get energies (should be the same for both)
    energies = dos1.energies
    
    # Compute difference for each spin channel
    densities_diff = {}
    for spin in dos1.densities.keys():
        if spin in dos2.densities:
            densities_diff[spin] = dos1.densities[spin] - dos2.densities[spin]
        else:
            densities_diff[spin] = dos1.densities[spin]
    
    # Create a new Dos object for the difference
    from pymatgen.electronic_structure.dos import Dos
    dos_diff = Dos(dos1.efermi, energies, densities_diff)
    
    return dos_diff

def create_zero_dos(reference_dos):
    """Create a DOS object with all zero densities, matching the reference DOS structure."""
    from pymatgen.electronic_structure.dos import Dos
    
    energies = reference_dos.energies
    densities_zero = {}
    
    for spin in reference_dos.densities.keys():
        densities_zero[spin] = np.zeros_like(reference_dos.densities[spin])
    
    return Dos(reference_dos.efermi, energies, densities_zero)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script.py <path_to_reference_directory>")
        sys.exit(1)
    
    ref_directory = sys.argv[1]
    current_directory = "."
    
    # Load DOS from both directories
    print(f"Loading DOS from current directory: {current_directory}")
    dos_current = load_dos(current_directory)
    
    print(f"Loading DOS from reference directory: {ref_directory}")
    dos_ref = load_dos(ref_directory)
    
    # Compute difference (current - reference)
    print("Computing DOS difference (current - reference)...")
    dos_diff = compute_dos_difference(dos_current, dos_ref)
    
    # Plot the difference
    plotter = DosPlotter()
    plotter.add_dos('DOS Difference (Current - Reference)', dos_diff)
    
    # Get elements from both structures
    elements_current = set(dos_current.structure.composition.elements)
    elements_ref = set(dos_ref.structure.composition.elements)
    
    # Get all unique elements
    all_elements = elements_current | elements_ref
    
    for element in all_elements:
        element_in_current = element in elements_current
        element_in_ref = element in elements_ref
        
        if element_in_current and element_in_ref:
            # Element in both: compute difference
            element_dos_current = dos_current.get_element_dos()[element]
            element_dos_ref = dos_ref.get_element_dos()[element]
            element_dos_diff = compute_dos_difference(element_dos_current, element_dos_ref)
            plotter.add_dos(f'{element} difference', element_dos_diff)
        elif element_in_current:
            # Element only in current: use positive (current - 0)
            element_dos_current = dos_current.get_element_dos()[element]
            zero_dos = create_zero_dos(element_dos_current)
            element_dos_diff = compute_dos_difference(element_dos_current, zero_dos)
            plotter.add_dos(f'{element} current', element_dos_diff)
        else:
            # Element only in reference: use negative (0 - reference)
            element_dos_ref = dos_ref.get_element_dos()[element]
            zero_dos = create_zero_dos(element_dos_ref)
            element_dos_diff = compute_dos_difference(zero_dos, element_dos_ref)
            plotter.add_dos(f'{element} reference', element_dos_diff)
    
    ax = plotter.get_plot()  # Get Axis object
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
        
        # Extract element name from label (e.g., "Ti Difference" -> "Ti")
        element_name = label.split()[0]
        
        if element_name in vesta_colors:
            line.set_color(vesta_colors[element_name])
        elif 'Difference' in label and label.startswith('DOS'):
            line.set_color('#000000')
        line.set_linewidth(1)
    
    # Add a horizontal line at y=0 for reference
    ax.axhline(y=0, color='gray', linestyle=':', linewidth=0.8, alpha=0.7)
    
    # Remove extra white space
    ax.margins(0)
    ax.autoscale_view()
    
    # Remove duplicate labels in legend for spin polarized DOS
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), fontsize='x-large')
    
    fig = plt.gcf()
    from python_utility.matplotlib.enable_interactive_plot import enable_scroll_zoom, enable_keyboard_pan
    enable_scroll_zoom(fig)
    enable_keyboard_pan(fig)
    plt.show()

sys.exit(0)