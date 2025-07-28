from ast import main
from math import exp
import re
import numpy as np
import os
import matplotlib
from scipy import special
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from latex_table import get_adjusted_prop
from sklearn.metrics import mean_absolute_error
from sklearn.linear_model import LinearRegression
from scipy.stats import pearsonr

matplotlib.rcParams.update({
    "text.usetex": True,
    "text.latex.preamble": r"\usepackage{amsmath}"
})
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
        "name": "CH3-H",
        "marker": "o",
        "filled": True,
    },
    "Boranil_I+RBINOL_H": {
        "name": "I-H",
        "marker": "s",
        "filled": True,
    },
    "Boranil_CF3+RBINOL_H": {
        "name": "CF3-H",
        "marker": "^",
        "filled": True,
    },
    "Boranil_SMe+RBINOL_H": {
        "name": "SMe-H",
        "marker": "D",
        "filled": True,
    },
    "Boranil_CN+RBINOL_H": {
        "name": "CN-H",
        "marker": "*",
        "filled": True,
    },
    "Boranil_NO2+RBINOL_H": {
        "name": "NO2-H",
        "marker": "X",
        "filled": True,
    },
    "Boranil_NH2+RBINOL_CN": {
        "name": "NH2-CN",
        "marker": "P",
        "filled": False,
    },
    "Boranil_I+RBINOL_CN": {
        "name": "I-CN",
        "marker": "s",
        "filled": False,
    },
    "Boranil_CN+RBINOL_CN": {
        "name": "CN-CN",
        "marker": "*",
        "filled": False,
    },
    "Boranil_NO2+RBINOL_CN": {
        "name": "NO2-CN",
        "marker": "X",
        "filled": False,
    },
}

visual_method_attributes = {
    "B3LYPtddft": {
        "name": "B3LYP",
        "color": "#1f77b4",
    },
    "PBE0tddft": {
        "name": "PBE0",
        "color": "#17becf",
    },
    "wB97X-D3tddft": {
        "name": r"$\boldsymbol{\omega}$B97X-D3",
        "color": "#1a9850",
    },
    "CAM-B3LYPtddft": {
        "name": "CAM-B3LYP",
        "color": "#a6d854",
    },
    "MO62Xtddft": {
        "name": "M06-2X",
        "color": "#8C564b",
    },
    "CISD": {
        "name": "CIS(D)",
        "color": "#9467bd",
    },
    "B2PLYPtddft": {
        "name": "B2PLYP",
        "color": "#e377c2",
    },
    "ADC2_COSMO": {
        "name": "ADC(2)",
        "color": "#ff7f0e",
    },
    "CC2_COSMO": {
        "name": "CC2",
        "color": "#d62728",
    },
}

def add_diagonal_reference_line(data_x, data_y, xylim=None):
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
    if xylim is not None:
        axis_min = xylim[0]
        axis_max = xylim[1]
    else:
        min_val = min(min(data_x), min(data_y))
        max_val = max(max(data_x), max(data_y))
        padding = 0.1 * (max_val - min_val)
        axis_min = min_val - padding
        axis_max = max_val + padding
    
    plt.plot([axis_min, axis_max], [axis_min, axis_max],
                color='gray', linestyle='--', alpha=0.5)

    plt.xlim(axis_min, axis_max)
    plt.ylim(axis_min, axis_max)
    try:
        if axis_max - max(data_x) >= min(data_x) - axis_min:
            loc= 'right'
        else:
            loc= 'left'
        return loc
    except Exception as e:
        print(f"Error determining location: {e}, defaulting to 'left'")
        return 'left'

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
    

def _common_save_plot(x_data, y_data, x_label, y_label, output_dir, output_filename, molecule_handles, axes_label_size, method_handles=None, xylim=None, loc=None):
    """
    Consolidated steps for adding a diagonal line, legends, labels, and saving the plot.
    """
    if not x_data or not y_data:
        print("No data to plot.")
        plt.close()
        return

    if loc is not None:
        _ = add_diagonal_reference_line(x_data, y_data, xylim=xylim)
        loc_molecule = loc
    else:
        loc = add_diagonal_reference_line(x_data, y_data, xylim=xylim)
        if method_handles:
            loc_molecule = f"lower {loc}"
            loc_method = f"upper {loc}"
        else:
            if loc == 'right':
                loc_molecule = 'lower right'
            else:
                loc_molecule = 'upper left'
    first_legend = plt.legend(handles=molecule_handles, loc=loc_molecule, 
                title=r'\textbf{Molecules}')
    if method_handles:
        plt.gca().add_artist(first_legend)
        plt.legend(handles=method_handles, loc=loc_method, title=r'\textbf{Methods}') # type: ignore
    plt.xlabel(fr"\textbf{{{x_label}}}", size=axes_label_size)
    plt.ylabel(fr"\textbf{{{y_label}}}", size=axes_label_size)
    plt.grid(alpha=0.2)
    plt.tight_layout()

    if output_dir is None:
        output_dir = "plot_comparison"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error: Unable to create or access the directory '{output_dir}'. Please check the path and permissions.")
        raise
    output_filename = output_filename.replace('None', '').replace(' ', '_').replace('ABS@', '').replace('FLUO@', '').replace('_-','_')
    output_filename = re.sub(r'_+', '_', output_filename)
    output_filename = output_filename.strip('_')
    try:
        plt.savefig(f"{output_dir}/{output_filename}.pdf", format='pdf')
        plt.savefig(f"{output_dir}/{output_filename}.png", format='png')
        print(f"Plot saved to {output_dir}/{output_filename} in format pdf and png")
    except Exception as e:
        print(f"Error saving plot {output_dir}/{output_filename}: {e}")
    plt.close()


def get_label(prop, luminescence_type, gauge=None):
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
    label = luminescence_type
    if prop == 'energy':
        label += ' Energy (eV)'
        axes_label_size = 26
    elif prop == 'dissymmetry_factor':
        if gauge not in ['length', 'velocity']:
            raise ValueError(f"Unknown gauge: {gauge}. Please set gauge to 'length' or 'velocity'.")
        label += f" Dissymmetry Factor in {gauge.capitalize()} Gauge"
        if luminescence_type == 'Absorption':
            label += r" ($\mathbf{g_{abs}}$"
        else:
            label += r" ($\mathbf{g_{fluo}}$"
        label += r", $\mathbf{\times 10^{-4}}$)"
        axes_label_size = 18
    else:
        raise ValueError(f"Unknown property: {prop}. Please set prop to 'energy' or 'dissymmetry_factor'.")
    return label, axes_label_size

def make_molecule_legend_handle(molecule_handles, molecule, color):
    if visual_molecule_attributes[molecule]["filled"]:
        facecolor=color
    else:
        facecolor='none'
    molecule_handles.append(Line2D([0], [0], marker=visual_molecule_attributes[molecule]["marker"], linestyle='None',
                                    markeredgecolor=color,
                                    markerfacecolor=facecolor,
                                    markersize=s_plot**0.5,
                                    label=fr"\textbf{{{visual_molecule_attributes[molecule]['name']}}}"))


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

    for method_optimization in methods_optimization:
        for method_luminescence in methods_luminescence:
            display_lum = method_luminescence.split('@')[1] if '@' in method_luminescence else method_luminescence
            color = visual_method_attributes[display_lum]["color"]
            calculated = []
            experimental = []
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
                make_molecule_legend_handle(molecule_handles, molecule, color)
            
            # Complete and save the plot if we have data
            if calculated:
                label_text, axes_label_size = get_label(prop, luminescence_type, gauge)
                _common_save_plot(
                    x_data=experimental,
                    y_data=calculated,
                    x_label=f"Experimental {label_text}",
                    y_label=f"Computed {label_text}",
                    output_dir=output_dir,
                    output_filename=f"{luminescence_type}_{prop}_{gauge}_{dissymmetry_variant}_{method_optimization}_{display_lum}_{output_filebasename}",
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
                    make_molecule_legend_handle(molecule_handles, molecule, 'black')
            if not molecule_legend_done:
                molecule_legend_done = True
            method_handles.append(Line2D([0], [0], color=visual_method_attributes[display_lum]["color"], lw=4, label=fr"\textbf{{{visual_method_attributes[display_lum]['name']}}}"))

    output_filename=f"{luminescence_type}_multiple_exp_{prop}_{gauge}_{dissymmetry_variant}_{output_filebasename}"
    if not all_calculated or not all_experimental:
        print(f"No data to plot for {output_filename}.")
        plt.close()
        return

    label_text, axes_label_size = get_label(prop, luminescence_type, gauge)
    _common_save_plot(
        x_data=all_experimental,
        y_data=all_calculated,
        x_label=f"Experimental {label_text}",
        y_label=f"Computed {label_text}",
        output_dir=output_dir,
        output_filename=output_filename,
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
                if molecule == "Boranil_NO2+RBINOL_H" and display_lum == 'B2PLYPTtddft':
                    continue
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
                    make_molecule_legend_handle(molecule_handles, molecule, "black")
            if not molecule_legend_done:
                molecule_legend_done = True
            method_handles.append(Line2D([0], [0], color=visual_method_attributes[display_lum]["color"], lw=4, label=fr"\textbf{{{visual_method_attributes[display_lum]['name']}}}"))
                    
                
    output_filename=f"{luminescence_type}_multiple_computed_{prop}_{gauge}_{dissymmetry_variant}_{output_filebasename}"
    if not all_calculated or not all_experimental:
        print(f"No data to plot for {output_filename}.")
        plt.close()
        return

    label_text, axes_label_size = get_label(prop, luminescence_type, gauge)
    display_main_lum = main_method_luminescence.split('@')[1] if '@' in main_method_luminescence else main_method_luminescence
    label_x = visual_method_attributes[display_main_lum]["name"]
    _common_save_plot(
        x_data=all_experimental,
        y_data=all_calculated,
        x_label=f"{label_x} {label_text}",
        y_label=f"Computed {label_text}",
        output_dir=output_dir,
        output_filename=output_filename,
        molecule_handles=molecule_handles,
        method_handles=method_handles,
        axes_label_size=axes_label_size
    )

def generate_plot_experiment_multiple_computed_rapport(
    exp_data: dict,
    luminescence_type: str,
    computed_data: dict,
    methods_optimization: list,
    methods_luminescence: list,
    prop: str,
    main_method_optimization: str="",
    main_method_luminescence: str="",
    padding=0.05,
    method_padding=0.1,
    va_above=[""],
    va_below=[""],
    output_filebasename="",
    output_dir="plot_comparison",
    gauge=None,
    dissymmetry_variant=None,
    molecules=None,
    banned_molecule=[""],
    xylim=None,
    Do_metrics=True,
    special_molecule=None,
):
    """
    Generate a comparison plot of experimental vs computed data for multiple methods, with trend lines and annotated statistics.

    This function plots experimental data against computed results for a set of molecules and methods, drawing a trend line for each method,
    and annotating the plot with the method name, mean absolute error (MAE), and R² value. It allows for custom placement of annotations and
    exclusion of specific molecules from the plot or trend calculation.

    Parameters
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
        Property to be plotted (e.g., 'energy', 'dissymmetry_factor').
    va_bottom : list
        List of method names for which the annotation vertical alignment should be 'bottom'.
    xlegend : float, optional
        X-coordinate for the statistics annotation (if separate from method name). If "auto", the annotation is automatically aligned.
    va_center : list, optional
        List of method names for which the annotation vertical alignment should be 'center'.
    output_filebasename : str, optional
        Base name for the output plot file.
    output_dir : str, optional
        Directory to save the plot.
    gauge : str, optional
        Gauge used in the calculations ('length' or 'velocity').
    dissymmetry_variant : str, optional
        Variant used in the dissymmetry factor calculations ('strength' or 'vector').
    molecules : list, optional
        List of molecules to include in the plot. If None, all molecules from exp_data will be used.
    banned_molecule : list[str], optional
        Molecule to exclude from plotting for B3LYP and PBE0.

    Returns
    -------
    None
        The function saves the plot to file and does not return a value.
    """
    # Handle default arguments
    if molecules is None:
        molecules = list(exp_data.keys()) 

    all_calculated = []
    all_experimental = []
    all_method_y = []
    method_handles = []
    molecule_handles = []
    molecule_legend_done = False
    max_len_method_name = max(max([len(visual_method_attributes[method_lum.split('@')[1]]['name']) if not method_lum.split('@')[1] == "wB97X-D3tddft" else 8  for method_lum in methods_luminescence]), 6)  # 6 is the length of 'Methods'
    max_len_method_name = 9
    method_x = None
    method_luminescence_name = main_method_luminescence.split('@')[1] if '@' in main_method_luminescence else main_method_luminescence
    for method_opt in methods_optimization:
        for method_lum in methods_luminescence:
            calculated = []
            experimental = []
            display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
            for molecule in molecules:
                adjusted_prop = get_adjusted_prop(prop, gauge, dissymmetry_variant)
                if not molecule_legend_done:
                    legend_color = '#E95329' if special_molecule and molecule in special_molecule else 'black'
                    make_molecule_legend_handle(molecule_handles, molecule, legend_color)
                if (molecule in computed_data and 
                    method_opt in computed_data[molecule] and 
                    method_lum in computed_data[molecule][method_opt] and
                    adjusted_prop in computed_data[molecule][method_opt][method_lum] and
                    not np.isnan(computed_data[molecule][method_opt][method_lum][adjusted_prop])):
                    calculated_data = computed_data[molecule][method_opt][method_lum][adjusted_prop]
                else:
                    continue

                if main_method_luminescence == "":
                    if (molecule in exp_data and 
                        luminescence_type in exp_data[molecule] and 
                        prop in exp_data[molecule][luminescence_type]):
                        experimental_data = exp_data[molecule][luminescence_type][prop]
                    else:
                        continue
                else:
                    if (molecule in exp_data and 
                    main_method_optimization in exp_data[molecule] and 
                    main_method_luminescence in exp_data[molecule][main_method_optimization] and
                    adjusted_prop in exp_data[molecule][main_method_optimization][main_method_luminescence] and
                    not np.isnan(exp_data[molecule][main_method_optimization][main_method_luminescence][adjusted_prop])):
                        experimental_data = exp_data[molecule][main_method_optimization][main_method_luminescence][adjusted_prop]
                    else:
                        continue

                if molecule in banned_molecule: #and (display_lum == 'B3LYPtddft' or display_lum == 'PBE0tddft'):
                    print(calculated_data, experimental_data, molecule, display_lum)
                    continue
                calculated.append(calculated_data)
                experimental.append(experimental_data)
                all_calculated.append(calculated_data)
                all_experimental.append(experimental_data)
                _plot(experimental_data, calculated_data, molecule, display_lum)

            if Do_metrics and not(method_lum == main_method_luminescence):
                MAE = mean_absolute_error(experimental, calculated)
                pearson_result = pearsonr(experimental, calculated)
                R2 = pearson_result[0] ** 2 # type: ignore
                if not (prop == 'dissymmetry_factor' and (display_lum == 'B3LYPtddft' or display_lum == 'PBE0tddft')):
                    model = LinearRegression().fit(np.array(experimental).reshape(-1, 1), np.array(calculated).reshape(-1, 1))
                else:
                    #return the index of the maximum and minimum value of experimental and remove the value correponding to this index from calculated and experimental
                    calculated = [x for i, x in enumerate(calculated) if i not in [i for i, x in enumerate(experimental) if x == max(experimental) or x == min(experimental)]]
                    experimental = [x for i, x in enumerate(experimental) if i not in [i for i, x in enumerate(experimental) if x == max(experimental) or x == min(experimental)]]
                    i = [i for i, x in enumerate(experimental) if x == max(experimental) or x == min(experimental)]
                    model = LinearRegression().fit(np.array(experimental).reshape(-1, 1), np.array(calculated).reshape(-1, 1))
                trend = model.predict(np.array(experimental).reshape(-1, 1))
                plt.plot(experimental, trend, linewidth=2,
                    color=visual_method_attributes[display_lum]["color"])
                size = 20
                if method_x is None:
                    method_x = max(experimental) + padding
                if model.coef_[0][0] > 0:
                    method_y = max(trend)
                else:
                    method_y = min(trend)
                all_method_y.append(method_y)
                if display_lum in va_above:
                    va = 'bottom'
                elif display_lum in va_below:
                    va = 'top'
                else:
                    va = 'center'
                plt.text(method_x, method_y,
                    s = f"\\makebox[{max_len_method_name*0.7}em][l]{{\\textbf{{{visual_method_attributes[display_lum]['name']}}}}} ({MAE:.2f}, {R2:.2f})",
                    size=size,
                    color=visual_method_attributes[display_lum]["color"],
                    ha='left', va=va)
                if not molecule_legend_done:
                    molecule_legend_done = True
                method_handles.append(Line2D([0], [0], color=visual_method_attributes[display_lum]["color"], lw=4, label=fr"\textbf{{{visual_method_attributes[display_lum]['name']}}}"))

    if Do_metrics:
        ylegend = max(all_method_y) + method_padding
        plt.text(method_x, ylegend, # type: ignore
            s=f"\\makebox[{max_len_method_name*0.7}em][l]{{\\textbf{{Method}}}} (MAE, $r^2$)",
            size=size, # type: ignore
            color='black',
            ha='left', va='bottom'
            )

    output_filename=f"Trend_{luminescence_type}_multiple_exp_{prop}_{gauge}_{dissymmetry_variant}_{output_filebasename}"
    if not all_calculated or not all_experimental:
        print(f"No data to plot for {output_filename}.")
        plt.close()
        return
    
    if method_luminescence_name in visual_method_attributes:
        xlabel = visual_method_attributes[method_luminescence_name]["name"]
    else:
        xlabel = "Experimental"
    label_text, axes_label_size = get_label(prop, luminescence_type, gauge)
    _common_save_plot(
        x_data=all_experimental,
        y_data=all_calculated,
        x_label=f"{xlabel} {label_text}",
        y_label=f"Computed {label_text}",
        output_dir=output_dir,
        output_filename=output_filename,
        molecule_handles=molecule_handles,
        axes_label_size=axes_label_size,
        loc='upper left',
        xylim=xylim
    )