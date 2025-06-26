import numpy as np
import os
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from latex_table import get_adjusted_prop

## Presentation parameters
#plt.rcParams.update({
#    'figure.figsize': [10, 10],
#    'font.size': 32,
#    'font.weight': 'bold',
#    'axes.labelweight': 'bold',
#    'axes.titlesize': 32,
#    'axes.titleweight': 'bold',
#    'legend.fontsize': 24,
#    'xtick.labelsize': 24,
#    'ytick.labelsize': 24
#})
#s_plot=140

# Normal parameters
plt.rcParams.update({
    'figure.figsize': [10, 10],
    'font.size': 24,
    'font.weight': 'bold',
    'axes.labelweight': 'bold',
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'legend.fontsize': 16,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
})
s_plot=80

visual_molecule_attributes = {
    "Boranil_CH3+RBINOL_H": {
        "name": "CH3_H",
        "marker": "o",
        "filled": True,
    },
    "Boranil_I+RBINOL_H": {
        "name": "I_H",
        "marker": "s",
        "filled": True,
    },
    "Boranil_CF3+RBINOL_H": {
        "name": "CF3_H",
        "marker": "^",
        "filled": True,
    },
    "Boranil_SMe+RBINOL_H": {
        "name": "SMe_H",
        "marker": "D",
        "filled": True,
    },
    "Boranil_CN+RBINOL_H": {
        "name": "CN_H",
        "marker": "*",
        "filled": True,
    },
    "Boranil_NO2+RBINOL_H": {
        "name": "NO2_H",
        "marker": "X",
        "filled": True,
    },
    "Boranil_NH2+RBINOL_CN": {
        "name": "NH2_CN",
        "marker": "P",
        "filled": False,
    },
    "Boranil_I+RBINOL_CN": {
        "name": "I_CN",
        "marker": "s",
        "filled": False,
    },
    "Boranil_CN+RBINOL_CN": {
        "name": "CN_CN",
        "marker": "*",
        "filled": False,
    },
    "Boranil_NO2+RBINOL_CN": {
        "name": "NO2_CN",
        "marker": "X",
        "filled": False,
    },
}

visual_method_attributes = {
    "B3LYPtddft": {
        "name": "B3LYP",
        "color": "#1f77b4",  # Dark blue
    },
    "PBE0tddft": {
        "name": "PBE0",
        "color": "#7eb3d6",  # Light blue
    },
    "wB97X-D3tddft": {
        "name": "omegaB97X-D3",
        "color": "#2ca02c",  # Dark green
    },
    "CAM-B3LYPtddft": {
        "name": "CAM-B3LYP",
        "color": "#98df8a",  # Medium green
    },
    "MO62Xtddft": {
        "name": "M06-2X",
        "color": "#5ad45a",  # Light green
    },
    "CISD": {
        "name": "CIS(D)",
        "color": "#d62728",  # Dark red
    },
    "B2PLYPtddft": {
        "name": "B2PLYP",
        "color": "#ff9896",  # Light red
    },
    "ADC2_COSMO": {
        "name": "ADC(2)",
        "color": "#9467bd",  # Dark purple
    },
    "CC2_COSMO": {
        "name": "CC2",
        "color": "#c5b0d5",  # Light purple
    },
}
                   

def add_diagonal_reference_line(data_x, data_y):
    """
    Add a diagonal reference line to the plot based on the range of two data sets, and adjust the x and y axis.
    
    Parameters:
    ----------
    data_x : list
        List of data points for the x-axis.
    data_y : list
        List of data points for the y-axis.
    
    Returns:
    -------
    axis_min : float
        Minimum value for the x and y axes.
    axis_max : float
        Maximum value for the x and y axes.
    """
    min_val = min(min(data_x), min(data_y))
    max_val = max(max(data_x), max(data_y))
    padding = 0.1 * (max_val - min_val)
    axis_min = min_val - padding
    axis_max = max_val + padding
    
    plt.plot([axis_min, axis_max], [axis_min, axis_max],
                color='gray', linestyle='--', alpha=0.5)

    plt.xlim(axis_min, axis_max)
    plt.ylim(axis_min, axis_max)

    return
    
def _plot(x, y, molecule, method):
    color = visual_method_attributes[method]["color"]
    if visual_molecule_attributes[molecule]["filled"]:
        facecolor =  color
    else:
        facecolor = 'none'
    plt.scatter(x, 
                y, 
                marker=visual_molecule_attributes[molecule]["marker"],
                edgecolor=color,
                facecolor=facecolor,
                s=s_plot,
                alpha=0.85,
                label=visual_molecule_attributes[molecule]["name"])
    

def _common_save_plot(x_data, y_data, x_label, y_label, output_dir, output_filename, molecule_handles, axes_label_size, method_handles=None):
    """
    Consolidated steps for adding a diagonal line, legends, labels, and saving the plot.
    """
    if not x_data or not y_data:
        print("No data to plot.")
        plt.close()
        return

    add_diagonal_reference_line(x_data, y_data)
    first_legend = plt.legend(handles=molecule_handles, loc='lower right', 
                title='Molecules')
    if method_handles:
        plt.gca().add_artist(first_legend)
        plt.legend(handles=method_handles, loc='upper right', title='Methods')
    plt.xlabel(x_label, size=axes_label_size)
    plt.ylabel(y_label, size=axes_label_size)
    plt.grid(alpha=0.2)
    #plt.tight_layout()

    if output_dir is None:
        output_dir = "plot_comparison"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error: Unable to create or access the directory '{output_dir}'. Please check the path and permissions.")
        raise
    try:
        plt.savefig(f"{output_dir}/{output_filename}.pdf", format='pdf')
        print(f"Plot saved to {output_dir}/{output_filename} in format pdf and png")
    except Exception as e:
        print(f"Error saving plot {output_dir}/{output_filename}: {e}")
    plt.close()


def get_label(prop, gauge=None):
    """
    Get the label for the plot based on the property and the gauge.
    Parameters:
    ----------
    prop : str
        The property to be plotted (e.g., 'energy', 'dissymmetry_factor').
    gauge : str, optional
        The gauge used in the calculations ('length' or 'velocity'). Default is None.
    Returns:
    -------
    str
        The label for the plot.
    """
    if prop == 'energy':
        label = 'Energy (eV)'
        axes_label_size = 20
    elif prop == 'dissymmetry_factor':
        if gauge == 'length':
            label = 'dissymmetry factor in length gauge (g)'
        elif gauge == 'velocity':
            label = 'dissymmetry factor in velocity gauge (g)'
        else:
            raise ValueError(f"Unknown gauge: {gauge}. Please set gauge to 'length' or 'velocity'.")
        axes_label_size = 16
    else:
        raise ValueError(f"Unknown property: {prop}. Please set prop to 'energy' or 'dissymmetry_factor'.")
    return label, axes_label_size


def generate_plot_experiment_computed(exp_data: dict, luminescence_type: str, computed_data: dict, methods_optimization: list, 
                                    methods_luminescence: list, prop: str, output_filebasename="", output_dir="plot_comparison",
                                    gauge=None, dissymmetry_variant=None, molecules=None):
    """
    Generate plots comparing experimental and computed data for electronic properties.
    Parameters:
    ----------
    exp_data : dict
        Experimental data for the molecules.
    luminescence_type : str
        Type of luminescence ('Absorption' or 'Fluorescence').
    computed_data : dict
        Computed data for the molecules.
    methods_optimization : list
        List of optimization methods used in the computations.
    methods_luminescence : list
        List of luminescence methods used in the computations.
    prop : str
        Property to be plotted (e.g., 'energy', 'dissymmetry_factor', etc.).
    output_filebasename : str, optional
        Name of the output file for the plot (without extention). Needed information will be added to the basename.
    output_dir : str, optional
        Directory where the plot will be saved. Default is "plot_comparison".
    gauge : str, optional
        Gauge used in the calculations ('length' or 'velocity').
    dissymmetry_variant : str, optional
        Variant used in the dissymmetry factor calculations ('strength' or 'vector').
    molecules : list, optional
        List of molecules to include in the plot. If None, all molecules from exp_data will be used.
    """
    # Handle default arguments
    if molecules is None:
        molecules = list(exp_data.keys())

    calculated = []
    experimental = []
    for method_optimization in methods_optimization:
        for method_luminescence in methods_luminescence:
            display_lum = method_luminescence.split('@')[1] if '@' in method_luminescence else method_luminescence
            color = visual_method_attributes[display_lum]["color"]
            molecule_handles = []
            for molecule in molecules:
                adjusted_prop = get_adjusted_prop(prop, gauge, dissymmetry_variant)
                if (molecule in computed_data and 
                    method_optimization in computed_data[molecule] and 
                    method_luminescence in computed_data[molecule][method_optimization] and
                    adjusted_prop in computed_data[molecule][method_optimization][method_luminescence] and
                    not np.isnan(computed_data[molecule][method_optimization][method_luminescence][adjusted_prop])):
                    calculated_data = computed_data[molecule][method_optimization][method_luminescence][adjusted_prop]
                else:
                    continue

                
                if (exp_data and 
                    molecule in exp_data and 
                    luminescence_type in exp_data[molecule] and 
                    prop in exp_data[molecule][luminescence_type]):
                    experimental_data = exp_data[molecule][luminescence_type][prop]
                else:
                    continue

                calculated.append(calculated_data)
                experimental.append(experimental_data)
                _plot(experimental_data, calculated_data, molecule, display_lum)
                if visual_molecule_attributes[molecule]["filled"]:
                    facecolor=color
                else:
                    facecolor='none'
                molecule_handles.append(Line2D([0], [0], marker=visual_molecule_attributes[molecule]["marker"], linestyle='None',
                                                markeredgecolor=color,
                                                markerfacecolor=facecolor,
                                                markersize=s_plot**0.5,
                                                label=visual_molecule_attributes[molecule]["name"]))
                    
            
            # Complete and save the plot if we have data
            if calculated:
                label_text, axes_label_size = get_label(prop, gauge)
                _common_save_plot(
                    x_data=experimental,
                    y_data=calculated,
                    x_label=f"Experimental {label_text}",
                    y_label=f"Computed {label_text}",
                    output_dir=output_dir,
                    output_filename=f"{output_filebasename}_{luminescence_type}_{method_optimization}_{method_luminescence}_{prop}",
                    molecule_handles=molecule_handles,
                    axes_label_size=axes_label_size

                )


def generate_plot_experiment_multiple_computed(exp_data: dict, luminescence_type: str, computed_data: dict, methods_optimization: list, 
                                    methods_luminescence: list, prop: str, output_filebasename="", output_dir="plot_comparison",
                                    gauge=None, dissymmetry_variant=None, molecules=None):
    """
    Generate plots comparing experimental and computed data for electronic properties.
    Parameters:
    ----------
    exp_data : dict
        Experimental data for the molecules.
    luminescence_type : str
        Type of luminescence ('Absorption' or 'Fluorescence').
    computed_data : dict
        Computed data for the molecules.
    methods_optimization : list
        List of optimization methods used in the computations.
    methods_luminescence : list
        List of luminescence methods used in the computations.
    prop : str
        Property to be plotted (e.g., 'energy', 'dissymmetry_factor', etc.).
    output_filebasename : str, optional
        Name of the output file for the plot (without extention). Needed information will be added to the basename.
    output_dir : str, optional
        Directory where the plot will be saved. Default is "plot_comparison".
    gauge : str, optional
        Gauge used in the calculations ('length' or 'velocity').
    dissymmetry_variant : str, optional
        Variant used in the dissymmetry factor calculations ('strength' or 'vector').
    molecules : list, optional
        List of molecules to include in the plot. If None, all molecules from exp_data will be used.
    """
    # Handle default arguments
    if molecules is None:
        molecules = list(exp_data.keys()) 

    all_calculated = []
    all_experimental = []
    method_handles = []
    molecule_handles = []
    molecule_legend_done = False
    for method_opt in methods_optimization:
        for method_lum in methods_luminescence:
            calculated = []
            experimental = []
            display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
            for molecule in molecules:
                adjusted_prop = get_adjusted_prop(prop, gauge, dissymmetry_variant)
                if (molecule in computed_data and 
                    method_opt in computed_data[molecule] and 
                    method_lum in computed_data[molecule][method_opt] and
                    adjusted_prop in computed_data[molecule][method_opt][method_lum] and
                    not np.isnan(computed_data[molecule][method_opt][method_lum][adjusted_prop])):
                    calculated_data = computed_data[molecule][method_opt][method_lum][adjusted_prop]
                else:
                    continue

                if (molecule in exp_data and 
                    luminescence_type in exp_data[molecule] and 
                    prop in exp_data[molecule][luminescence_type]):
                    experimental_data = exp_data[molecule][luminescence_type][prop]
                else:
                    continue

                calculated.append(calculated_data)
                all_calculated.append(calculated_data)
                experimental.append(experimental_data)
                all_experimental.append(experimental_data)
                _plot(experimental_data, calculated_data, molecule, display_lum)
                if not molecule_legend_done:
                    color = 'black'
                    if visual_molecule_attributes[molecule]["filled"]:
                        facecolor=color
                    else:
                        facecolor='none'
                    molecule_handles.append(Line2D([0], [0], marker=visual_molecule_attributes[molecule]["marker"], linestyle='None',
                                                    markeredgecolor=color,
                                                    markerfacecolor=facecolor,
                                                    markersize=s_plot**0.5,
                                                    label=visual_molecule_attributes[molecule]["name"]))
            if not molecule_legend_done:
                molecule_legend_done = True
            method_handles.append(Line2D([0], [0], color=visual_method_attributes[display_lum]["color"], lw=4, label=visual_method_attributes[display_lum]["name"]))
                    
                
    if not all_calculated or not all_experimental:
        print("No data to plot.")
        plt.close()
        return

    label_text, axes_label_size = get_label(prop, gauge)
    _common_save_plot(
        x_data=all_experimental,
        y_data=all_calculated,
        x_label=f"Experimental {label_text}",
        y_label=f"Computed {label_text}",
        output_dir=output_dir,
        output_filename=f"{output_filebasename}_{luminescence_type}_multiple_exp_{prop}",
        molecule_handles=molecule_handles,
        method_handles=method_handles,
        axes_label_size=axes_label_size
    )


def generate_plot_computed_multiple_computed(main_method_optimization: str, main_method_luminescence: str, luminescence_type: str, computed_data: dict, 
                                             methods_optimization: list, methods_luminescence: list, prop: str,
                                             output_filebasename=None, output_dir="plot_comparison",
                                             molecule_name_mapping=None, method_colors=None, label=None,
                                             gauge=None, dissymmetry_variant=None, molecules=None):
    """
    Generate plots comparing computed data against a main method for electronic properties.
    Parameters:
    ----------
    main_method_optimization : str
        Main optimization method used in the computations. Will be plot on the x axis.
    main_method_luminescence : str
        Main luminescence method used in the computations. Will be plot on the x axis.
    luminescence_type : str
        Type of luminescence ('Absorption' or 'Fluorescence').
    computed_data : dict
        Computed data for the molecules.
    methods_optimization : list
        List of optimization methods used in the computations.
    methods_luminescence : list
        List of luminescence methods used in the computations.
    prop : str
        Property to be plotted (e.g., 'energy', 'dissymmetry_factor', etc.).
    output_filebasename : str, optional
        Name of the output file for the plot (without extention). Needed information will be added to the basename.
    output_dir : str, optional
        Directory where the plot will be saved. Default is "plot_comparison".
    molecule_name_mapping : dict, optional
        Mapping of molecule names to display-friendly names for tables and plots.
    marker_color : list[str], optional
        Color of the dots in the plot. Default color is blue for absorption, red for fluorescence, and black otherwise.
    label : str, optional
        Label for the axes and the title. If None, the default label is the property.
    gauge : str, optional
        Gauge used in the calculations ('length' or 'velocity').
    dissymmetry_variant : str, optional
        Variant used in the dissymmetry factor calculations ('strength' or 'vector').
    molecules : list, optional
        List of molecules to include in the plot. If None, all molecules from exp_data will be used.
    """
    # Handle default arguments
    if molecules is None:
        molecules = list(computed_data.keys())

    all_calculated = []
    all_experimental = []
    method_handles = []
    molecule_handles = []
    molecule_legend_done = False
    for method_opt in methods_optimization:
        for method_lum in methods_luminescence:
            calculated = []
            experimental = []
            display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
            for molecule in molecules:
                # Get the computed data
                adjusted_prop = get_adjusted_prop(prop, gauge, dissymmetry_variant)
                if (molecule in computed_data and 
                    method_opt in computed_data[molecule] and 
                    method_lum in computed_data[molecule][method_opt] and
                    adjusted_prop in computed_data[molecule][method_opt][method_lum] and
                    not np.isnan(computed_data[molecule][method_opt][method_lum][adjusted_prop])):
                    calculated_data = computed_data[molecule][method_opt][method_lum][adjusted_prop]
                else:
                    continue
                
                # Get the experimental data
                if (molecule in computed_data and 
                    method_opt in computed_data[molecule] and 
                    method_lum in computed_data[molecule][main_method_optimization] and
                    adjusted_prop in computed_data[molecule][main_method_optimization][main_method_luminescence] and
                    not np.isnan(computed_data[molecule][main_method_optimization][main_method_luminescence][adjusted_prop])):
                    main_method_data = computed_data[molecule][main_method_optimization][main_method_luminescence][adjusted_prop]
                else:
                    continue

                # If both data are found add the data to the lists
                calculated.append(calculated_data)
                all_calculated.append(calculated_data)
                experimental.append(main_method_data)
                all_experimental.append(main_method_data)
                _plot(main_method_data, calculated_data, molecule, display_lum)
                if not molecule_legend_done:
                    color = 'black'
                    if visual_molecule_attributes[molecule]["filled"]:
                        facecolor=color
                    else:
                        facecolor='none'
                    molecule_handles.append(Line2D([0], [0], marker=visual_molecule_attributes[molecule]["marker"], linestyle='None',
                                                    markeredgecolor=color,
                                                    markerfacecolor=facecolor,
                                                    markersize=s_plot**0.5,
                                                    label=visual_molecule_attributes[molecule]["name"]))
            if not molecule_legend_done:
                molecule_legend_done = True
            method_handles.append(Line2D([0], [0], color=visual_method_attributes[display_lum]["color"], lw=4, label=visual_method_attributes[display_lum]["name"]))
                    
                
    if not all_calculated or not all_experimental:
        print("No data to plot.")
        plt.close()
        return
    
    label_text, axes_label_size = get_label(prop, gauge)
    display_main_lum = main_method_luminescence.split('@')[1] if '@' in main_method_luminescence else main_method_luminescence
    label_x = visual_method_attributes[display_main_lum]["name"]
    _common_save_plot(
        x_data=all_experimental,
        y_data=all_calculated,
        x_label=f"{label_x} {label_text}",
        y_label=f"Computed {label_text}",
        output_dir=output_dir,
        output_filename=f"{output_filebasename}_{luminescence_type}_multiple_computed_{prop}",
        molecule_handles=molecule_handles,
        method_handles=method_handles,
        axes_label_size=axes_label_size
    )