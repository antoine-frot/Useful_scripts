#! /home/afrot/virtual_env_python/bin/python3
import matplotlib.pyplot as plt
import warnings
# Filter out the specific networkx warning occuring on taz
warnings.filterwarnings("ignore", message="networkx backend defined more than once: nx-loopback")
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.plotter import DosPlotter
from workflow_tools.vasp.vesta_colors import vesta_colors

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