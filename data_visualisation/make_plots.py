import numpy as np
import os
import re
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
from latex_table import get_adjusted_prop

def add_diagonal_reference_line(data_x, data_y):
    """
    Add a diagonal reference line to the plot based on the range of two data sets, and return the axis limits.
    
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

    return axis_min, axis_max
    
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
    molecule_markers = {}
    available_markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x']
    
    # Create molecule to marker mapping
    for i, molecule in enumerate(molecule_data):
        molecule_markers[molecule] = available_markers[i % len(available_markers)]
    
    # 1. INDIVIDUAL METHOD PLOTS
    # Make sure the output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error: Unable to create or access the directory '{output_dir}'. Please check the path and permissions.")
        raise
    for method_opt in methods_optimization:
        for method_lum in methods_luminescence:
            plt.figure(figsize=(10, 8))

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
                axis_min, axis_max = add_diagonal_reference_line(experimental, calculated)
                
                # Create legend with unique labels (no duplicates)
                handles, labels = plt.gca().get_legend_handles_labels()
                by_label = dict(zip(labels, handles))
                plt.legend(by_label.values(), by_label.keys(), title='Molecules')
                
                plt.xlim(axis_min, axis_max)
                plt.ylim(axis_min, axis_max)
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
                    plt.savefig(f"{output_dir}/{output_filename}.pdf", format='pdf')
                    plt.savefig(f"{output_dir}/{output_filename}.png")
                    print(f"Plot saved to {output_dir}/{output_filename}.pdf and {output_dir}/{output_filename}.png")
                except Exception as e:
                    print(f"Error saving plot {output_dir}/{output_filename}: {e}")


            plt.close()

def generate_plot_experiment_multiple_computed(exp_data: dict, luminescence_type: str, computed_data: dict, methods_optimization: list, 
                                    methods_luminescence: list, prop: str, output_filebasename=None, output_dir="plot_comparison",
                                    molecule_name_mapping=None, dot_color=None, label=None,
                                    gauge=None, dissymmetry_variant=None, title=None, molecules=None):
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
        Name of the output file for the plot. Needed information will be added to the basename.
    output_dir : str, optional
        Directory where the plot will be saved. Default is "plot_comparison".
    molecule_name_mapping : dict, optional
        Mapping of molecule names to display-friendly names for tables and plots.
    dot_color : str, optional
        Color of the dots in the plot. Default color is blue for absorption, red for fluorescence, and black otherwise.
    label : str, optional
        Label for the x and y axes. If None, a default label will be generated based on the property.
    gauge : str, optional
    dissymmetry_variant : str, optional
    title : str, optional
        Title for the plot. If None, a default title will be generated.
    molecules : list, optional
        List of molecules to include in the plot. If None, all molecules from exp_data will be used.
    """
    # Handle default arguments
    if molecules is None:
        molecules = list(exp_data.keys()) if isinstance(exp_data, dict) else [item["name"] for item in exp_data]
    molecule_data = exp_data if isinstance(exp_data, dict) else {item["name"]: item for item in exp_data}

    if dot_color is None:
        if luminescence_type == "Absorption":
            dot_color = "blue"
        elif luminescence_type == "Fluorescence":
            dot_color = "red"
        else:
            dot_color = "black"
    
    # Assign unique markers to each molecule
    molecule_markers = {}
    available_markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x']
    
    # Create molecule to marker mapping
    for i, molecule in enumerate(molecule_data):
        molecule_markers[molecule] = available_markers[i % len(available_markers)]
    
    # 1. INDIVIDUAL METHOD PLOTS
    # Make sure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    for method_opt in methods_optimization:
        for method_lum in methods_luminescence:
            plt.figure(figsize=(12, 9))

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
                        color=dot_color,
                        s=80,  # Larger points
                        alpha=0.8,
                        label=display_name)
            
            # Complete and save the plot if we have data
            if not len(calculated) == 0:
                axis_min, axis_max = add_diagonal_reference_line(experimental, calculated)
                
                # Create legend with unique labels (no duplicates)
                handles, labels = plt.gca().get_legend_handles_labels()
                by_label = dict(zip(labels, handles))
                plt.legend(by_label.values(), by_label.keys(), title='Molecules')
                
                plt.xlim(axis_min, axis_max)
                plt.ylim(axis_min, axis_max)
                if label is None:
                    label = f"{' '.join(prop.split('_'))}"
                plt.xlabel(f"Experimental {label}")
                plt.ylabel(f"Computed {label}")
                plt.grid(alpha=0.2)
                plt.tight_layout()
                display_opt = method_opt.split('@')[1] if '@' in method_opt else method_opt
                display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
                method_name = f"{display_opt}-{display_lum}".lstrip("-")
                if title is None:
                    if gauge is not None and dissymmetry_variant is not None:
                        title = f"{luminescence_type} ({gauge}, {dissymmetry_variant}) {label} of experimental data against {method_name} computed data."
                    else:
                        title = f"{luminescence_type} {label} of experimental data against {method_name} computed data."
                plt.title(f"{title}")
                if output_filebasename is None:
                    if gauge is not None and dissymmetry_variant is not None:
                        output_filename = f"{luminescence_type}_{method_name}_{prop}_{gauge}_{dissymmetry_variant}.pdf"
                    else:
                        output_filename = f"{luminescence_type}_{method_name}_{prop}.pdf"
                else:
                    if gauge is not None and dissymmetry_variant is not None:
                        output_filename = f"{output_filebasename}_{luminescence_type}_{method_name}_{prop}_{gauge}_{dissymmetry_variant}.pdf"
                    else:
                        output_filename = f"{output_filebasename}_{luminescence_type}_{method_name}_{prop}.pdf"
                plt.savefig(f"{output_dir}/{output_filename}")
                print(f"Plot saved to {output_dir}/{output_filename}")
            plt.close()

#def global_plots():
#    # 2. GLOBAL PLOTS
#    # 2.1 GLOBAL ABSORPTION PLOT
#    all_abs_x, all_abs_y = [], []
#    
#    # Plot data for each method with consistent coloring
#    for method_idx, method in enumerate(METHODS):
#        if all_abs_data[method]:  # Only if there's data for this method
#            color = plt.cm.tab10.colors[method_idx % len(plt.cm.tab10.colors)]
#            
#            for exp_val, comp_val, molecule_name, marker in all_abs_data[method]:
#                all_abs_x.append(exp_val)
#                all_abs_y.append(comp_val)
#                plt.scatter(exp_val, comp_val,
#                           marker=marker,
#                           color=color,
#                           s=80,
#                           alpha=0.8)
#    
#    # Complete the absorption global plot if we have data
#    if all_abs_x and all_abs_y:
#        # Add diagonal reference line
#        min_val = min(min(all_abs_x), min(all_abs_y))
#        max_val = max(max(all_abs_x), max(all_abs_y))
#        padding = 0.1 * (max_val - min_val)
#        axis_min = min_val - padding
#        axis_max = max_val + padding
#        
#        plt.plot([axis_min, axis_max], [axis_min, axis_max],
#                color='gray', linestyle='--', alpha=0.5)
#        
#        # Create legends (molecules and methods)
#        from matplotlib.lines import Line2D
#        
#        # Method color legend
#        method_handles = []
#        for i, method in enumerate(METHODS):
#                color = cm.tab10.colors[i % len(cm.tab10.colors)]
#                color = plt.cm.tab10.colors[i % len(plt.cm.tab10.colors)]
#                method_handles.append(Line2D([0], [0], color=color, lw=4, label=method))
#        
#        # Molecule marker legend  
#        molecule_handles = []
#        for molecule, marker in molecule_markers.items():
#            if exp_data[molecule]['display']:
#                display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
#                molecule_handles.append(Line2D([0], [0], marker=marker, color='black', 
#                                             markersize=8, linestyle='None', label=display_name))
#        
#        # Add the legends
#        first_legend = plt.legend(handles=molecule_handles, loc='upper left', 
#                                 title='Molecules', fontsize=9)
#        plt.gca().add_artist(first_legend)
#        
#        plt.legend(handles=method_handles, loc='lower right', 
#                  title='Methods', fontsize=9)
#        
#        plt.xlim(axis_min, axis_max)
#        plt.ylim(axis_min, axis_max)
#        plt.title("Absorption: Experimental vs Computed Energies (All Methods)")
#        plt.xlabel("Experimental Energy (eV)")
#        plt.ylabel("Computed Energy (eV)")
#        plt.grid(alpha=0.2)
#        plt.tight_layout()
#        plt.savefig("plot_comparison/absorption_comparison.pdf")
#    plt.close()