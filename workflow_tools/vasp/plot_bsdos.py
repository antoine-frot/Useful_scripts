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

vesta_colors = {
    "H":   "#ffcccc",
    "He":  "#fce8ce",
    "Li":  "#86df73",
    "Be":  "#5ed77b",
    "B":   "#1fa20f",
    "C":   "#4c4c4c",
    "N":   "#b0b9e6",
    "O":   "#fe0300",
    "F":   "#b0b9e6",
    "Ne":  "#fe37b5",
    "Na":  "#f9dc3c",
    "Mg":  "#fb7b15",
    "Al":  "#81b2d6",
    "Si":  "#1b3bfa",
    "P":   "#c09cc2",
    "S":   "#fffa00",
    "Cl":  "#31fc02",
    "Ar":  "#cffec4",
    "K":   "#a121f6",
    "Ca":  "#5a96bd",
    "Sc":  "#b563ab",
    "Ti":  "#78caff",
    "V":   "#e51900",
    "Cr":  "#00009e",
    "Mn":  "#a7089d",
    "Fe":  "#b57100",
    "Co":  "#0000af",
    "Ni":  "#b7bbbd",
    "Cu":  "#2247dc",
    "Zn":  "#8f8f81",
    "Ga":  "#9ee373",
    "Ge":  "#7e6ea6",
    "As":  "#74d057",
    "Se":  "#9aef0f",
    "Br":  "#7e3102",
    "Kr":  "#fac1f3",
    "Rb":  "#702eb0",
    "Sr":  "#00ff00",
    "Y":   "#94ffff",
    "Zr":  "#00ff00",
    "Nb":  "#73c2c9",
    "Mo":  "#54b5b5",
    "Tc":  "#3b9e9e",
    "Ru":  "#248f8f",
    "Rh":  "#0a7d8c",
    "Pd":  "#006985",
    "Ag":  "#c0c0c0",
    "Cd":  "#ffd98f",
    "In":  "#a67573",
    "Sn":  "#9a8eb9",
    "Sb":  "#9e63b5",
    "Te":  "#d47a00",
    "I":   "#940094",
    "Xe":  "#429eb0",
    "Cs":  "#57178f",
    "Ba":  "#00c900",
    "La":  "#5ac449",
    "Ce":  "#ffffc7",
    "Pr":  "#d9ffc7",
    "Nd":  "#c7ffc7",
    "Pm":  "#a3ffc7",
    "Sm":  "#8fffc7",
    "Eu":  "#61ffc7",
    "Gd":  "#45ffc7",
    "Tb":  "#30ffc7",
    "Dy":  "#1fffc7",
    "Ho":  "#00ff9c",
    "Er":  "#00e675",
    "Tm":  "#00d452",
    "Yb":  "#00bf38",
    "Lu":  "#00ab24",
    "Hf":  "#4dc2ff",
    "Ta":  "#4da6ff",
    "W":   "#2194d6",
    "Re":  "#267dab",
    "Os":  "#266696",
    "Ir":  "#175487",
    "Pt":  "#d0d0e0",
    "Au":  "#ffd123",
    "Hg":  "#b8b8d0",
    "Tl":  "#a6544d",
    "Pb":  "#575961",
    "Bi":  "#9e4fb5",
    "Po":  "#ab5c00",
    "At":  "#754f45",
    "Rn":  "#428296",
    "Fr":  "#420066",
    "Ra":  "#007d00",
    "Ac":  "#70abfa",
    "Th":  "#00baff",
    "Pa":  "#00a1ff",
    "U":   "#008fff",
    "Np":  "#0080ff",
    "Pu":  "#006bff",
    "Am":  "#545cf2",
    "Cm":  "#785ce3",
    "Bk":  "#8a4fe3",
    "Cf":  "#a136d4",
    "Es":  "#b31fd4",
    "Fm":  "#b31fba",
    "Md":  "#b30da6",
    "No":  "#bd0d87",
    "Lr":  "#c70066",
    "Rf":  "#cc0059",
    "Db":  "#d1004f",
    "Sg":  "#d90045",
    "Bh":  "#e00038",
    "Hs":  "#e6002e",
    "Mt":  "#eb0026",
    "Ds":  "#eb0026",   # (same as Mt in scheme)
    "Rg":  "#eb0026",
    "Cn":  "#eb0026",
    "Nh":  "#eb0026",
    "Fl":  "#eb0026",
    "Mc":  "#eb0026",
    "Lv":  "#eb0026",
    "Ts":  "#eb0026",
    "Og":  "#eb0026",
}

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