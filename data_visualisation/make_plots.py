from turtle import title
import numpy as np
import os
import re
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
from collections import OrderedDict
from matplotlib.lines import Line2D
from latex_table import get_adjusted_prop

plt.rcParams.update({
    'figure.figsize': [10, 10],
    'font.size': 32,
    'font.weight': 'bold',
    'axes.labelweight': 'bold',
    'axes.titlesize': 32,
    'axes.titleweight': 'bold',
    'legend.fontsize': 24,
    'xtick.labelsize': 24,
    'ytick.labelsize': 24
})
s_plot=140

available_markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x']
additional_markers = ['1', '2', '3', '4', '8', '|', '_'] 
available_markers.extend(additional_markers)
molecule_markers = {}

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
    
def generate_plot_experiment_computed(exp_data: dict, luminescence_type: str, computed_data: dict, methods_optimization: list, 
                                    methods_luminescence: list, prop: str, output_filebasename=None, output_dir="plot_comparison",
                                    molecule_name_mapping=None, marker_color=None, label=None,
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
    molecule_name_mapping : dict, optional
        Mapping of molecule names to display-friendly names for tables and plots.
    method_colors : list, optional
        List of colors to use for different methods in the plot. If None, default colors from the matplotlib colormap will be used.
    marker_color : str, optional
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
        molecules = list(exp_data.keys()) if isinstance(exp_data, dict) else [item["name"] for item in exp_data]
    molecule_data = exp_data if isinstance(exp_data, dict) else {item["name"]: item for item in exp_data}

    if marker_color is None:
        if luminescence_type == "Absorption":
            marker_color = "blue"
        elif luminescence_type == "Fluorescence":
            marker_color = "red"
        else:
            marker_color = "black"
    
    # Assign unique markers to each molecule
    if len(molecules) > len(available_markers) + len(molecule_markers):
        raise ValueError("Not enough markers available for the number of molecules. Please provide a list of markers.")
    for molecule in molecules:
        if molecule not in molecule_markers:
            molecule_markers[molecule] = available_markers.pop(0)
    
    # Make sure the output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error: Unable to create or access the directory '{output_dir}'. Please check the path and permissions.")
        raise
    for method_opt in methods_optimization:
        for method_lum in methods_luminescence:
            calculated = []
            experimental = []
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
                if (molecule_data and 
                    molecule in molecule_data and 
                    luminescence_type in molecule_data[molecule] and 
                    prop in molecule_data[molecule][luminescence_type]):
                    experimental_data = molecule_data[molecule][luminescence_type][prop]
                else:
                    continue

                # If both data are found add the data to the lists
                calculated.append(calculated_data)
                experimental.append(experimental_data)
                    
                # Plot the molecule data
                marker = molecule_markers[molecule]
                if molecule_name_mapping is None:
                    display_name = molecule
                else:
                    display_name = molecule_name_mapping.get(molecule, molecule)
                plt.scatter(experimental_data, calculated_data, 
                        marker=marker, 
                        color=marker_color,
                        s=80,  # Larger points
                        alpha=0.8,
                        label=display_name)
            
            # Complete and save the plot if we have data
            if calculated:
                add_diagonal_reference_line(experimental, calculated)
                
                # Create legend with unique labels (no duplicates)
                handles, legend_labels = plt.gca().get_legend_handles_labels()
                by_label = OrderedDict(zip(legend_labels, handles))
                plt.legend(by_label.values(), by_label.keys(), title='Molecules')
                
                if label is None:
                    label = f"{' '.join(prop.split('_'))}"
                plt.xlabel(f"Experimental {label}")
                plt.ylabel(f"Computed {label}")
                plt.grid(alpha=0.2)

                display_opt = method_opt.split('@')[1] if '@' in method_opt else method_opt
                display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
                method_name = f"{display_opt}-{display_lum}".lstrip("-")

                if gauge is not None and dissymmetry_variant is not None:
                    title_text = f"{luminescence_type} ({gauge}, {dissymmetry_variant}) {label} of experimental data against {method_name} computed data."
                else:
                    title_text = f"{luminescence_type} {label} of experimental data against {method_name} computed data."
                plt.title(title_text)

                plt.tight_layout()

                if output_filebasename is None:
                    if gauge is not None and dissymmetry_variant is not None:
                        output_filename = f"{luminescence_type}_{method_name}_{prop}_{gauge}_{dissymmetry_variant}"
                    else:
                        output_filename = f"{luminescence_type}_{method_name}_{prop}"
                else:
                    if gauge is not None and dissymmetry_variant is not None:
                        output_filename = f"{output_filebasename}_{luminescence_type}_{method_name}_{prop}_{gauge}_{dissymmetry_variant}"
                    else:
                        output_filename = f"{output_filebasename}_{luminescence_type}_{method_name}_{prop}"
                
                output_filename = re.sub(r'[<>:"/\\|?*]', '_', output_filename)
                try:
                    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists
                    plt.savefig(f"{output_dir}/{output_filename}.pdf", format='pdf')
                    plt.savefig(f"{output_dir}/{output_filename}.png")
                    print(f"Plot saved to {output_dir}/{output_filename}.pdf and {output_dir}/{output_filename}.png")
                except Exception as e:
                    print(f"Error saving plot {output_dir}/{output_filename}: {e}")


            plt.close()

def generate_plot_experiment_multiple_computed(exp_data: dict, luminescence_type: str, computed_data: dict, methods_optimization: list, 
                                    methods_luminescence: list, prop: str, output_filebasename=None, output_dir="plot_comparison",
                                    molecule_name_mapping=None, method_colors=None, label=None,
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
        molecules = list(exp_data.keys()) if isinstance(exp_data, dict) else [item["name"] for item in exp_data]
    molecule_data = exp_data if isinstance(exp_data, dict) else {item["name"]: item for item in exp_data}

    # Assign unique markers to each molecule
    if len(molecules) > len(available_markers) + len(molecule_markers):
        raise ValueError("Not enough markers available for the number of molecules. Please provide a list of markers.")
    for molecule in molecules:
        if molecule not in molecule_markers:
            molecule_markers[molecule] = available_markers.pop(0)

    method_color = {}
    available_colors = method_colors if method_colors is not None else plt.cm.tab10.colors # type: ignore
                
    # Make sure the output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error: Unable to create or access the directory '{output_dir}'. Please check the path and permissions.")
        raise
    all_calculated = []
    all_experimental = []
    method_names = []
    counter = 0
    for method_opt in methods_optimization:
        for method_lum in methods_luminescence:
            display_opt = method_opt.split('@')[1] if '@' in method_opt else method_opt
            display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
            method_name = f"{display_opt}-{display_lum}".lstrip("-")
            method_names.append(method_name)
            if counter >= len(available_colors):
                raise ValueError("Not enough colors available for the number of methods. Please provide a list of colors.")
            method_color[method_name] = available_colors[counter]
            counter += 1

            calculated = []
            experimental = []
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
                if (molecule_data and 
                    molecule in molecule_data and 
                    luminescence_type in molecule_data[molecule] and 
                    prop in molecule_data[molecule][luminescence_type]):
                    experimental_data = molecule_data[molecule][luminescence_type][prop]
                else:
                    continue

                # If both data are found add the data to the lists
                calculated.append(calculated_data)
                all_calculated.append(calculated_data)
                experimental.append(experimental_data)
                all_experimental.append(experimental_data)
                    
                # Plot the molecule data
                color = method_color[method_name]
                marker = molecule_markers[molecule]
                if molecule_name_mapping is None:
                    display_name = molecule
                else:
                    display_name = molecule_name_mapping.get(molecule, molecule)
                plt.scatter(experimental_data, calculated_data, 
                        marker=marker, 
                        color=color,
                        s=80,  # Larger points
                        alpha=0.8,
                        label=display_name)
                
    if not all_calculated or not all_experimental:
        print("No data to plot.")
        plt.close()
        return
    
    add_diagonal_reference_line(all_experimental, all_calculated)

    method_handles = []
    for i, method in enumerate(method_names):
        if method in method_color:
            color = method_color[method]
            method_handles.append(Line2D([0], [0], color=color, lw=4, label=method))
    
    # Molecule marker legend  
    molecule_handles = []
    for molecule, marker in molecule_markers.items():
        if molecule_name_mapping is None:
            display_name = molecule
        else:
            display_name = molecule_name_mapping.get(molecule, molecule)
        molecule_handles.append(Line2D([0], [0], marker=marker, color='black', 
                                        markersize=8, linestyle='None', label=display_name))
    
    # Add the legends
    first_legend = plt.legend(handles=molecule_handles, loc='lower right', 
                                title='Molecules')
    plt.gca().add_artist(first_legend)
    
    plt.legend(handles=method_handles, loc='upper right', 
                title='Methods')
    
    if label is None:
        label = f"{' '.join(prop.split('_'))}"
    plt.xlabel(f"Experimental {label}")
    plt.ylabel(f"Computed {label}")
    plt.grid(alpha=0.2)

    if gauge is not None and dissymmetry_variant is not None:
        title_text = f"{luminescence_type} ({gauge}, {dissymmetry_variant}) {label} of experimental data against computed data."
    else:
        title_text = f"{luminescence_type} {label} of experimental data against computed data."
    plt.title(title_text)

    plt.tight_layout()

    if output_filebasename is None:
        if gauge is not None and dissymmetry_variant is not None:
            output_filename = f"{luminescence_type}_multiple_{prop}_{gauge}_{dissymmetry_variant}"
        else:
            output_filename = f"{luminescence_type}_multiple_{prop}"
    else:
        if gauge is not None and dissymmetry_variant is not None:
            output_filename = f"{output_filebasename}_{luminescence_type}_multiple_{prop}_{gauge}_{dissymmetry_variant}"
        else:
            output_filename = f"{output_filebasename}_{luminescence_type}_multiple_{prop}"
    output_filename = re.sub(r'[<>:"/\\|?*]', '_', output_filename)
    try:
        plt.savefig(f"{output_dir}/{output_filename}.pdf", format='pdf')
        plt.savefig(f"{output_dir}/{output_filename}.png")
        print(f"Plot saved to {output_dir}/{output_filename}.pdf and {output_dir}/{output_filename}.png")
    except Exception as e:
        print(f"Error saving plot {output_dir}/{output_filename}: {e}")
    plt.close()

def generate_plot_computed_multiple_computed(main_method_optimization: str, main_method_luminescence: str, luminescence_type: str, computed_data: dict, methods_optimization: list, 
                                    methods_luminescence: list, prop: str, output_filebasename=None, output_dir="plot_comparison",
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
        molecules = list(computed_data.keys()) if isinstance(computed_data, dict) else [item["name"] for item in computed_data]
    molecule_data = computed_data if isinstance(computed_data, dict) else {item["name"]: item for item in computed_data}

    # Assign unique markers to each molecule
    if len(molecules) > len(available_markers) + len(molecule_markers):
        raise ValueError("Not enough markers available for the number of molecules. Please provide a list of markers.")
    for molecule in molecules:
        if molecule not in molecule_markers:
            molecule_markers[molecule] = available_markers.pop(0)

    method_color = {}
    available_colors = method_colors if method_colors is not None else plt.cm.tab10.colors # type: ignore
                
    # Make sure the output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error: Unable to create or access the directory '{output_dir}'. Please check the path and permissions.")
        raise
    all_calculated = []
    all_experimental = []
    method_names = []
    counter = 0
    for method_opt in methods_optimization:
        for method_lum in methods_luminescence:
            display_opt = method_opt.split('@')[1] if '@' in method_opt else method_opt
            display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
            method_name = f"{display_opt}-{display_lum}".lstrip("-")
            method_names.append(method_name)
            if counter >= len(available_colors):
                raise ValueError("Not enough colors available for the number of methods. Please provide a list of colors.")
            method_color[method_name] = available_colors[counter]
            counter += 1

            calculated = []
            experimental = []
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
                if (molecule_data and 
                    molecule in molecule_data and 
                    luminescence_type in molecule_data[molecule] and 
                    prop in molecule_data[molecule][luminescence_type]):
                    experimental_data = molecule_data[molecule][luminescence_type][prop]
                else:
                    continue

                # If both data are found add the data to the lists
                calculated.append(calculated_data)
                all_calculated.append(calculated_data)
                experimental.append(experimental_data)
                all_experimental.append(experimental_data)
                    
                # Plot the molecule data
                color = method_color[method_name]
                marker = molecule_markers[molecule]
                if molecule_name_mapping is None:
                    display_name = molecule
                else:
                    display_name = molecule_name_mapping.get(molecule, molecule)
                plt.scatter(experimental_data, calculated_data, 
                        marker=marker, 
                        color=color,
                        s=80,  # Larger points
                        alpha=0.8,
                        label=display_name)
                
    if not all_calculated or not all_experimental:
        print("No data to plot.")
        plt.close()
        return
    
    # Add diagonal reference line
    add_diagonal_reference_line(all_experimental, all_calculated)

    # Create legends (molecules and methods)
    from matplotlib.lines import Line2D
    
    # Method color legend
    method_handles = []
    for i, method in enumerate(method_names):
        if method in method_color:
            color = method_color[method]
            method_handles.append(Line2D([0], [0], color=color, lw=4, label=method))
    
    # Molecule marker legend  
    molecule_handles = []
    for molecule, marker in molecule_markers.items():
        if molecule_name_mapping is None:
            display_name = molecule
        else:
            display_name = molecule_name_mapping.get(molecule, molecule)
        molecule_handles.append(Line2D([0], [0], marker=marker, color='black', 
                                        markersize=8, linestyle='None', label=display_name))
    
    # Add the legends
    first_legend = plt.legend(handles=molecule_handles, loc='lower right', 
                                title='Molecules')
    plt.gca().add_artist(first_legend)
    
    plt.legend(handles=method_handles, loc='upper right', 
                title='Methods')
    
    if label is None:
        label = f"{' '.join(prop.split('_'))}"
    plt.xlabel(f"Experimental {label}")
    plt.ylabel(f"Computed {label}")
    plt.grid(alpha=0.2)

    if gauge is not None and dissymmetry_variant is not None:
        title_text = f"{luminescence_type} ({gauge}, {dissymmetry_variant}) {label} of experimental data against computed data."
    else:
        title_text = f"{luminescence_type} {label} of experimental data against computed data."
    plt.title(title_text)

    plt.tight_layout()

    if output_filebasename is None:
        if gauge is not None and dissymmetry_variant is not None:
            output_filename = f"{luminescence_type}_multiple_{prop}_{gauge}_{dissymmetry_variant}"
        else:
            output_filename = f"{luminescence_type}_multiple_{prop}"
    else:
        if gauge is not None and dissymmetry_variant is not None:
            output_filename = f"{output_filebasename}_{luminescence_type}_multiple_{prop}_{gauge}_{dissymmetry_variant}"
        else:
            output_filename = f"{output_filebasename}_{luminescence_type}_multiple_{prop}"
    output_filename = re.sub(r'[<>:"/\\|?*]', '_', output_filename)
    try:
        plt.savefig(f"{output_dir}/{output_filename}.pdf", format='pdf')
        plt.savefig(f"{output_dir}/{output_filename}.png")
        print(f"Plot saved to {output_dir}/{output_filename}.pdf and {output_dir}/{output_filename}.png")
    except Exception as e:
        print(f"Error saving plot {output_dir}/{output_filename}: {e}")
    plt.close()

def PhD_Day(exp_data: dict, computed_data: dict, output_dir="plot_comparison",
                                    molecule_name_mapping=None, method_colors=None, label=None,
                                    gauge=None, dissymmetry_variant=None, molecules=None):
    """
    special function to generate the plot for the PhD day
    """
    # Handle default arguments
    if molecules is None:
        molecules = list(exp_data.keys()) if isinstance(exp_data, dict) else [item["name"] for item in exp_data]
    molecule_data = exp_data if isinstance(exp_data, dict) else {item["name"]: item for item in exp_data}

    # Assign unique markers to each molecule
    method_color = {}
    available_colors = method_colors if method_colors is not None else plt.cm.tab10.colors # type: ignore
                
    # Make sure the output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error: Unable to create or access the directory '{output_dir}'. Please check the path and permissions.")
        raise
    all_calculated = []
    all_experimental = []
    method_names = []
    counter = 0
    prop = "energy"
    luminescence_type = "Absorption"
    for method_opt in [""]:
        for method_lum in ["ABS@MO62Xtddft","ABS@ADC2_COSMO"]:
            display_opt = method_opt.split('@')[1] if '@' in method_opt else method_opt
            display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
            method_name = f"{display_opt}-{display_lum}".lstrip("-")
            method_names.append(method_name)
            if counter >= len(available_colors):
                raise ValueError("Not enough colors available for the number of methods. Please provide a list of colors.")
            method_color[method_name] = available_colors[counter]
            counter += 1

            calculated = []
            experimental = []
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
                if (molecule_data and 
                    molecule in molecule_data and 
                    luminescence_type in molecule_data[molecule] and 
                    prop in molecule_data[molecule][luminescence_type]):
                    experimental_data = molecule_data[molecule][luminescence_type][prop]
                else:
                    continue

                # If both data are found add the data to the lists
                calculated.append(calculated_data)
                all_calculated.append(calculated_data)
                experimental.append(experimental_data)
                all_experimental.append(experimental_data)
                    
            # Plot the molecule data
            if method_lum == "ABS@ADC2_COSMO":
                color = plt.cm.tab10.colors[1]
                marker = 's'
                method = "Post HF: ADC(2)"
            else:
                color = plt.cm.tab10.colors[0]
                marker = 'o'
                method = "TDDFT: M06-2X "
            plt.scatter(experimental, calculated, 
                    marker=marker, 
                    color=color,
                    s=140,  # Larger points
                    alpha=0.8,
                    label=method)
            
    if not all_calculated or not all_experimental:
        print("No data to plot.")
        plt.close()
        return
    
    add_diagonal_reference_line(all_experimental, all_calculated)

    if label is None:
        label = f"{' '.join(prop.split('_'))}"
    plt.xlabel(f"Experimental {label}")
    plt.ylabel(f"Computed {label}")
    plt.grid(alpha=0.2)
    plt.legend(title='Methods', loc='upper right')
    plt.tight_layout()

    output_filename = "PhD_Day"
    output_filename = re.sub(r'[<>:"/\\|?*]', '_', output_filename)
    try:
        plt.savefig(f"{output_dir}/{output_filename}.pdf", format='pdf')
        plt.savefig(f"{output_dir}/{output_filename}.png")
        plt.savefig(f"{output_dir}/{output_filename}.svg")
        print(f"Plot saved to {output_dir}/{output_filename}.pdf and {output_dir}/{output_filename}.png")
    except Exception as e:
        print(f"Error saving plot {output_dir}/{output_filename}: {e}")
    plt.close()
