#! /home/afrot/virtual_env_python/bin/python3
import matplotlib.pyplot as plt
import os
import sys
import shutil
import filecmp
import warnings
# Filter out the specific networkx warning occuring on taz
warnings.filterwarnings("ignore", message="networkx backend defined more than once: nx-loopback")
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.plotter import BSPlotter

def get_band_structure_properties(band_structure):
    """
    Returns a list of strings containing the properties.
    """
    lines = ['Material Properties:\n']
    if band_structure.is_metal():
        lines.append('Material is metallic\n')
    else:
        band_gap = band_structure.get_band_gap()
        if band_gap['direct']:
            lines.append(f"Direct band gap of {band_gap['energy']:.4f} eV\n")
        else:
            lines.append(f"Indirect band gap of {band_gap['energy']:.4f} eV for transition {band_gap['transition']}\n")
            direct_gap = band_structure.get_direct_band_gap()
            lines.append(f"Direct Gap: {direct_gap:.4f} eV\n")
            
    return lines

source_path = os.path.realpath(sys.argv[0])
dest_path = os.path.join(os.getcwd(), os.path.basename(source_path))
print(source_path, "->", dest_path)
print() # New line for better readability if the script is run in background
if os.path.exists(dest_path):
    # Compare files content
    if not filecmp.cmp(source_path, dest_path, shallow=False):
        print("Warning: Local copy already exists in this folder. Run this version instead:")
        print(f"python3 {os.path.basename(sys.argv[0])}")
        sys.exit(0)

try:
    shutil.copy(source_path, dest_path)
    print(f"Copied script {os.path.basename(source_path)} to current folder")
except Exception as e:
    print(f"Failed to copy script {os.path.basename(source_path)}: {e}")

# Load band structure from vasprun.xml
vasprun = Vasprun("vasprun.xml")
bs = vasprun.get_band_structure()
print("".join(get_band_structure_properties(bs)))
with open("band_structure_properties.txt", "w") as f:
    f.writelines(get_band_structure_properties(bs))

plotter = BSPlotter(bs)
ax = plotter.get_plot(vbm_cbm_marker=True) # Plot with VBM and CBM markers
fig_bs = plt.gcf()
from python_utility.matplotlib.enable_interactive_plot import enable_scroll_zoom, enable_keyboard_pan
enable_scroll_zoom(fig_bs)
enable_keyboard_pan(fig_bs)
plt.show()