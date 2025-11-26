#! /home/afrot/virtual_env_python/bin/python3
import matplotlib.pyplot as plt
import warnings
import matplotlib.colors as mcolors
# Filter out the specific networkx warning occuring on taz
warnings.filterwarnings("ignore", message="networkx backend defined more than once: nx-loopback")
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.plotter import BSDOSPlotter
# Suppress matplotlib font warnings
import logging
logging.getLogger('matplotlib.font_manager').disabled = True
from workflow_tools.vasp.vesta_colors import vesta_colors

vasprun_bs = Vasprun("bandstructure/vasprun.xml", parse_projected_eigen=True)
bs = vasprun_bs.get_band_structure()
vasprun_dos = Vasprun("postprocessing/vasprun.xml")
dos = vasprun_dos.complete_dos
bsdosplot = BSDOSPlotter(bs_projection="elements",
                         dos_projection="elements")
plt_result = bsdosplot.get_plot(bs, dos=dos)
fig = plt.gcf()
axes = fig.axes  # axes[0] = Band Structure, axes[1] = DOS

def normalize_color(color):
    """Converts any color to hex for safe comparison."""
    try:
        # Handles single colors
        return mcolors.to_hex(color).lower()
    except ValueError:
        # Handles cases where color might be a list (like in collections)
        try:
            return mcolors.to_hex(color[0]).lower()
        except:
            return None

def repaint_axis(ax, element_colors):
    """
    Identifies elements by their existing color on the plot, 
    then repaints everything (Lines, Collections/Fills, Legend).
    """
    # 1. DETECTIVE WORK: Map { Old_Color_Hex : Element_Name }
    # We use get_legend_handles_labels() which works even if the Legend object is broken
    handles, labels = ax.get_legend_handles_labels()
    
    old_color_map = {}
    
    for handle, label in zip(handles, labels):
        c = None
        # Try to get color from various object types
        if hasattr(handle, 'get_color'):        # Lines
            c = handle.get_color()
        elif hasattr(handle, 'get_facecolor'):  # Patches/Fills
            c = handle.get_facecolor()
            
        c_hex = normalize_color(c)
        if c_hex:
            old_color_map[c_hex] = label

    # 2. REPAINT LINES (Band Structure segments)
    for line in ax.get_lines():
        current_hex = normalize_color(line.get_color())
        if current_hex in old_color_map:
            element = old_color_map[current_hex]
            if element in element_colors:
                line.set_color(element_colors[element])

    # 3. REPAINT COLLECTIONS (Filled DOS areas)
    # DOS fills are often 'PolyCollection' objects, stored in ax.collections
    for collection in ax.collections:
        # Collections store colors as a list, usually we check the first one
        current_hex = normalize_color(collection.get_facecolor())
        if current_hex in old_color_map:
            element = old_color_map[current_hex]
            if element in element_colors:
                new_color = element_colors[element]
                collection.set_facecolor(new_color)
                collection.set_edgecolor(new_color)
    
    # 4. REPAINT PATCHES (Legacy filled areas)
    for patch in ax.patches:
        current_hex = normalize_color(patch.get_facecolor())
        if current_hex in old_color_map:
            element = old_color_map[current_hex]
            if element in element_colors:
                patch.set_facecolor(element_colors[element])
                patch.set_edgecolor(element_colors[element])

    ax.legend(loc='best')


repaint_axis(axes[0], vesta_colors)
repaint_axis(axes[1], vesta_colors)
axes[0].set_title("Band Structure", fontsize=16)
axes[1].set_title("Density of States", fontsize=16)
plt.tight_layout()
plt.show()