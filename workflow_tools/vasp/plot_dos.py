#! /home/afrot/virtual_env_python/bin/python3
import matplotlib.pyplot as plt
import warnings
# Filter out the specific networkx warning occuring on taz
warnings.filterwarnings("ignore", message="networkx backend defined more than once: nx-loopback")
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.plotter import DosPlotter

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

vasprun = Vasprun("vasprun.xml", parse_projected_eigen=True)
dos = vasprun.complete_dos # Total DOS + projection on atoms and orbitals

plotter = DosPlotter()
plotter.add_dos('Total DOS', dos)
plotter.add_dos_dict(dos.get_element_dos())
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
    if label in vesta_colors:
        line.set_color(vesta_colors[label])
    elif label == 'Total DOS':
        line.set_color('#000000')
    line.set_linewidth(1)
# Remove extra white space
ax.margins(0)
ax.autoscale_view()
# Remove duplicate labels in legend for spin polarized DOS
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax.legend(by_label.values(), by_label.keys(), fontsize='x-large')
fig = plt.gcf()        # Get current figure
from python_utility.matplotlib_helper_functions import enable_scroll_zoom, enable_keyboard_pan
enable_scroll_zoom(fig)
enable_keyboard_pan(fig)
plt.show()               # Display