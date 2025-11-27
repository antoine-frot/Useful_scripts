#!/usr/bin/env python3
"""
LaTeX Table Generator for Computational Chemistry Data
=====================================================

This module provides functions for generating LaTeX tables from electronic transition
and circular dichroism computational chemistry data.

Please check main function `generate_latex_table` for usage and parameters.
"""

from matplotlib import table
import numpy as np
from pathlib import Path
from scipy.stats import pearsonr


def get_property_header(property_name, data_type):
    """
    Get LaTeX header for a given property and data type.
    
    Parameters
    ----------
    property_name : str
        Name of the property (e.g., 'energy', 'wavelength')
    data_type : str
        Type of data ('Absorption' or 'Fluorescence')
        
    Returns
    -------
    str
        LaTeX formatted header for the property
    """
    headers = {
        "wavelength": {
            "Absorption": "$\\lambda_{\\text{Abs}}$ (nm)",
            "Fluorescence": "$\\lambda_{\\text{Fluo}}$ (nm)"
        },
        "energy": {
            "Absorption": "E$_{\\text{Abs}}$ (eV)",
            "Fluorescence": "E$_{\\text{Fluo}}$ (eV)"
        },
        "oscillator_strength": {
            "Absorption": "fosc$_{\\text{Abs}}$/$\\epsilon$",
            "Fluorescence": "fosc$_{\\text{Fluo}}$/$\\Phi_\\text{f}$"
        },
        "oscillator_strength_length": {
            "Absorption": "fosc$_{\\text{Abs}}$(length)",
            "Fluorescence": "fosc$_{\\text{Fluo}}$(length)"
        },
        "oscillator_strength_velocity": {
            "Absorption": "fosc$_{\\text{Abs}}$(velocity)",
            "Fluorescence": "fosc$_{\\text{Fluo}}$(velocity)"
        },
        "rotational_strength": {
            "Absorption": "R$_{\\text{Abs}}$",
            "Fluorescence": "R$_{\\text{Fluo}}$"
        },
        "rotational_strength_length": {
            "Absorption": "R$_{\\text{Abs}}$",
            "Fluorescence": "R$_{\\text{Fluo}}$"
        },
        "rotational_strength_velocity": {
            "Absorption": "R$^{\\text{vel}}_{\\text{Abs}}$",
            "Fluorescence": "R$^{\\text{vel}}_{\\text{Fluo}}$"
        },
        "dipole_strength": {
            "Absorption": "D$_{\\text{Abs}}$",
            "Fluorescence": "D$_{\\text{Fluo}}$"
        },
        "dipole_strength_length": {
            "Absorption": "D$_{\\text{Abs}}$",
            "Fluorescence": "D$_{\\text{Fluo}}$"
        },
        "dipole_strength_velocity": {
            "Absorption": "D$^{\\text{vel}}_{\\text{Abs}}$",
            "Fluorescence": "D$^{\\text{vel}}_{\\text{Fluo}}$"
        },
        "dissymmetry_factor": {
            "Absorption": "$g_{\\text{abs}}$ ($10^{-4}$)",
            "Fluorescence": "$g_{\\text{lum}}$ ($10^{-4}$)"
        },
        "dissymmetry_factor_strength_length": {
            "Absorption": "$g_{\\text{abs}}$ ($10^{-4}$)",
            "Fluorescence": "$g_{\\text{lum}}$ ($10^{-4}$)"
        },
        "dissymmetry_factor_strength_velocity": {
            "Absorption": "$g_{\\text{abs}}^{\\text{vel}}$ ($10^{-4}$)",
            "Fluorescence": "$g_{\\text{lum}}^{\\text{vel}}$ ($10^{-4}$)"
        },
        "angle_length": {
            "Absorption": "$\\theta_{\\text{MD}}$ ($^\\circ$)",
            "Fluorescence": "$\\theta_{\\text{MD}}$ ($^\\circ$)"
        },
        "angle_velocity": {
            "Absorption": "$\\theta_{\\text{MP}}$ ($^\\circ$)",
            "Fluorescence": "$\\theta_{\\text{MP}}$ ($^\\circ$)"
        }
    }
    
    if property_name in headers and data_type in headers[property_name]:
        return headers[property_name][data_type]
    return f"{property_name}-{data_type}"

def format_value(data, property_name):
    """
    Format a value for LaTeX table according to property type.
    
    Parameters
    ----------
    data : dict
        Dictionary containing the property value
    property_name : str
        Name of the property to format
    
    Returns
    -------
    str
        Formatted value as string
    """
    value = data.get(property_name, np.nan)
    
    if isinstance(value, (int, float)) and not np.isnan(value):
        if property_name == "wavelength":
            return f"{value:.0f}"
        elif property_name in ["energy"]:
            return f"{value:.2f}"
        elif property_name.startswith("oscillator"):
            return f"{value:.2f}"
        elif property_name.startswith("rotational_strength"):
            return f"{value:.1f}"
        elif property_name.startswith("dipole_strength"):
            return f"{value:.0f}"
        elif property_name.startswith("dissymmetry_factor"):
            return f"{value:.2f}"
        elif property_name.startswith("angle"):
            return f"{value:.0f}"
        elif property_name == "D2" or property_name == "P2" or property_name == "M2":
            return f"{value:.2f}"
        else:
            return f"{value:.2f}"
    return "N/A"

def generate_table_header(properties, data_types):
    """
    Generate LaTeX table header for selected properties.
    
    Parameters
    ----------
    properties : list
        List of property names to include in header
    data_types : list
        List of data types ('Absorption', 'Fluorescence') to include
        
    Returns
    -------
    str
        LaTeX formatted table header
    """
    header = "    Molecule & Method"
    for data_type in data_types:
        for prop in properties:
            header += f" & {get_property_header(prop, data_type)}"
    return header + "\\\\"

def get_adjusted_prop(prop, gauge=None, variant=None):
    """Get the right property name based on gauge and property type."""

    # Validate gauge and variant
    if gauge not in ["length", "velocity", None]:
        raise ValueError(f"Invalid gauge: {gauge}")
    if variant not in ["strength", "vector", None]:
        raise ValueError(f"Invalid dissymmetry_variant: {variant}")

    # Adjust property name based on gauge and variant
    gauge_dependent = ['oscillator_strength', 'rotational_strength', 'dipole_strength', 'angle']
    
    if gauge and prop in gauge_dependent:
        adjusted_prop = f"{prop}_{gauge}"
    elif gauge and variant and prop == 'dissymmetry_factor':
        adjusted_prop = f"dissymmetry_factor_{variant}_{gauge}"
    else:
        adjusted_prop = prop
    return adjusted_prop

def generate_latex_table(exp_data: dict, luminescence_type: str, computed_data: dict, methods_optimization: list, 
                         methods_luminescence: list, properties: list, output_filename, output_dir="latex_tables", gauges: list[str] = ['length', 'velocity'], 
                         dissymmetry_variants: list[str] = ['vector', 'strength'], 
                         molecule_name_mapping=None, caption=None, label=None, molecules=None):
    """
    Generate LaTeX tables for the specified properties and data types.
    
    Parameters
    ----------
    exp_data : dict
        Dictionary of experimental data
    luminescence_type : str
        Type of luminescence ('Absorption' or 'Fluorescence')
    computed_data : dict
        Dictionary of computed data
    methods_optimization : list
        List of optimization methods
    methods_luminescence : list
        List of luminescence methods
    properties : list
        List of property names to include in the table
    gauges : list
        List of gauges to include (default: ['length', 'velocity'])
    dissymmetry_variants : list
        List of dissymmetry factor calculation variants to include (default: ['vector', 'strength'])
    molecule_name_mapping : dict
        Dictionary mapping molecule names to display names
    caption : str
        Caption for the table
    label_prefix : str
        Prefix for the table label
    output_filename : str
        Filename to save the LaTeX table
    molecules : list or None
        List of molecule names to include (default: all molecules in exp_data)
        
    Returns
    -------
    None
        Prints LaTeX table code to standard output
    """
    # Use provided methods or globals
    molecule_name_mapping = molecule_name_mapping or globals().get('MOLECULE_NAME_MAPPING', {})
    
    # Standardize data format
    if molecules is None:
        molecules = list(exp_data.keys()) if isinstance(exp_data, dict) else [item["name"] for item in exp_data]
    molecule_data = exp_data if isinstance(exp_data, dict) else {item["name"]: item for item in exp_data}

    # Handle defaults arguments
    if label is None:
        label = f"tab:{luminescence_type}_{properties}_{gauges}_{dissymmetry_variants}"
    if caption is None:
        caption = f"{luminescence_type} ({gauges}, {dissymmetry_variants}) chiroptical data for the studied molecules."
    
    # Helper functions
    def get_property_value(data_dict, prop, gauge=None, variant=None):
        """Get property value with gauge handling"""
        if not data_dict:
            return "N/A"
        adjusted_prop = get_adjusted_prop(prop, gauge, variant)
        return format_value(data_dict, adjusted_prop)
    
    def create_row(row_name, data_dict, props, gauge=None, variant=None):
        """Create a table row with appropriate formatting"""
        row_name = ' '.join(row_name.split('_'))
        if variant: # if variant is defined gauge should be defined too
            row = [f"{row_name} ({gauge}, {variant})"]
        elif gauge:
            row = [f"{row_name} ({gauge})"]
        else:
            row = [row_name]
            
        has_data = False
        
        for prop in props:
            value = get_property_value(data_dict, prop, gauge, variant)
            row.append(value)
            if value != "N/A" and value != "":
                has_data = True
                
        return row, has_data
    
    # Open output file for writing
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(output_dir) / output_filename, 'w') as f:
        # Helper function to write to file
        def writeline(line=""):
            f.write(line + "\n")
        def table_header():
            writeline("\\begin{table}[H]")
            writeline("  \\centering")
            writeline("  \\scriptsize")
            column_spec = "ll" + "c" * len(properties)
            writeline(f"  \\begin{{tabular}}{{{column_spec}}}")
            writeline("    \\toprule")
            writeline(generate_table_header(properties, [luminescence_type]))
            writeline("    \\midrule")
        def table_footer(caption, label, table_num):
            writeline("    \\bottomrule")
            writeline("  \\end{tabular}")
            if not caption:
                caption = f"{luminescence_type} ({gauges}, {dissymmetry_variants}) chiroptical data for the studied molecules." 
            writeline(f"  \\caption{{{caption} (Part {table_num})}}")
            if not label:
                label = f"table_{luminescence_type}_{gauges}_{dissymmetry_variants}"
            writeline(f"  \\label{{tab:{label}{table_num}}}")
            writeline("\\end{table}\n\n")

        # Variable to limit the size of the table
        table_num = 0
        table_rows = 0
        max_rows = 65

        table_header()
        
        # Table content
        for molecule in molecules:
            if molecule not in molecule_data:
                continue
                
            display_name = molecule_name_mapping.get(molecule, molecule)
            
            # Experimental row
            exp_data_for_molecule = molecule_data[molecule].get(luminescence_type, {})
            exp_row, _ = create_row("Exp", exp_data_for_molecule, properties)
            
            # Computed rows
            computed_rows = []
            
            for method_opt in methods_optimization:
                display_opt = method_opt.split('@')[1] if '@' in method_opt else method_opt
                
                for method_lum in methods_luminescence:
                    display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
                    
                    # Check if we need to handle gauges
                    has_dissymmetry = 'dissymmetry_factor' in properties
                    gauge_dependent_props = ['oscillator_strength', 'rotational_strength', 'dipole_strength', 'angle']
                    use_gauges = any(prop in properties for prop in gauge_dependent_props) or has_dissymmetry
                    
                    for gauge in (gauges if use_gauges else [None]):
                        method_data = {}
                        if (molecule in computed_data and 
                            method_opt in computed_data[molecule] and 
                            method_lum in computed_data[molecule][method_opt]):
                            method_data = computed_data[molecule][method_opt][method_lum]
                        
                        # Base method name
                        base_name = f"{display_opt}-{display_lum}" 
                        base_name = base_name.lstrip('-')
                        
                        # Create rows for each property
                        for variant in (dissymmetry_variants if has_dissymmetry else [None]):
                            row, has_data = create_row(base_name, method_data, properties, gauge, variant)
                            if has_data and (not has_dissymmetry or len(properties) > 1):
                                computed_rows.append(row)
                            
            
            # writeline rows
            table_rows += len(computed_rows) + 3 # 2 for experimental row and 1 for midrule
            if table_rows > max_rows:
                table_num += 1
                table_rows = len(computed_rows) + 3
                table_footer(caption, label, table_num)
                table_header()
            else:
                writeline("    \\midrule")
            multirow_count = len(computed_rows) + 1
            writeline(f"    \\multirow{{{multirow_count}}}{{*}}{{{display_name}}} & " + " & ".join(exp_row) + " \\\\\\\\")
            
            for row in computed_rows:
                writeline(f"     & " + " & ".join(row) + " \\\\")
            
        
        # Table footer
        table_footer(caption, label, table_num)
    print(f"Latex table saved to {output_dir}/{output_filename}")

def generate_latex_metrics_table(exp_data: dict, luminescence_type: str, computed_data: dict, methods_optimization: list, 
                         methods_luminescence: list, prop: str, warnings_list, output_filename=None, output_dir="latex_tables", 
                         gauge=None, dissymmetry_variant=None, caption=None, label=None, molecules=None):
    """Print LaTeX code for the metrics summary table."""
    # Standardize data format
    if molecules is None:
        molecules = list(exp_data.keys()) if isinstance(exp_data, dict) else [item["name"] for item in exp_data]
    molecule_data = exp_data if isinstance(exp_data, dict) else {item["name"]: item for item in exp_data}

    # Handle defaults arguments
    if label is None:
        label = f"tab:metric_{luminescence_type}_{prop}_{gauge}_{dissymmetry_variant}"
    if caption is None:
        caption = f"{luminescence_type} ({gauge}, {dissymmetry_variant}) chiroptical metric data for the studied molecules."
    
    # Make the table
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if output_filename is None:
        if gauge is None and dissymmetry_variant is None:
            output_filename = f"{luminescence_type}_{prop}_data.tex"
        else:
            output_filename = f"{luminescence_type}_{prop}_{gauge}_{dissymmetry_variant}_data.tex"

    with open(Path(output_dir) / output_filename, 'w') as f:
        # Helper function to write to file
        def writeline(line=""):
            f.write(line + "\n")
        writeline("\\begin{table}[htbp]")
        writeline("  \\centering")
        writeline("  \\begin{tabular}{lrrrr}")
        writeline("    \\toprule")
        writeline("    Method & MSE & MAE & SD & R$^2$ \\\\")
        writeline("    \\midrule")
        
        
        for method_opt in methods_optimization:
            display_opt = method_opt.split('@')[1] if '@' in method_opt else method_opt
            
            for method_lum in methods_luminescence:
                # Base method name
                display_lum = method_lum.split('@')[1] if '@' in method_lum else method_lum
                base_name = f"{display_opt}-{display_lum}" 
                base_name = base_name.lstrip('-')
                base_name = ' '.join(base_name.split('_'))
                if dissymmetry_variant: # if variant is defined gauge should be defined too
                    base_name = f"{base_name} ({gauge}, {dissymmetry_variant})"
                elif gauge:
                    base_name = f"{base_name} ({gauge})"
                
                # Get the data
                calculated = []
                experimental = []
                warnings_list_temp = []
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
                        warnings_list_temp.append(f"Warning: Computational value for {prop} is missing for {molecule} using {base_name} for {luminescence_type}.")
                        continue
                    
                    # Get the experimental data
                    if (molecule_data and 
                        molecule in molecule_data and 
                        luminescence_type in molecule_data[molecule] and 
                        prop in molecule_data[molecule][luminescence_type]):
                        experimental_data = molecule_data[molecule][luminescence_type][prop]
                    else:
                        warnings_list_temp.append(f"Warning: Experimental value for {prop} is missing for {molecule}.")
                        continue

                    # If both data are found add the data to the lists
                    calculated.append(calculated_data)
                    experimental.append(experimental_data)

                # Calculate metrics
                if len(calculated) == 0:
                    continue
                else:
                    warnings_list.extend(warnings_list_temp)
                    errors = [c - e for c, e in zip(calculated, experimental)]
                    mse = np.mean(errors) if errors else np.nan
                    mae = np.mean(np.abs(errors)) if errors else np.nan
                    sd = np.std(errors) if len(errors) > 1 else np.nan
                    r_sq = np.nan
                    if len(calculated) >= 2:
                        pearson_result = pearsonr(experimental, calculated)
                        r_sq = pearson_result[0] ** 2 # type: ignore
                    mse_str = f"{mse:.2f}" if not np.isnan(mse) else 'N/A'
                    mae_str = f"{mae:.2f}" if not np.isnan(mae) else 'N/A'
                    sd_str = f"{sd:.2f}" if not np.isnan(sd) else 'N/A'
                    r_sq_str = f"{r_sq:.2f}" if not np.isnan(r_sq) else 'N/A'
                
                writeline(f"    {base_name} & {mse_str} & {mae_str} & {sd_str} & {r_sq_str} \\\\")
        writeline("    \\bottomrule")
        writeline("  \\end{tabular}")
        if not caption:
            caption = f"{luminescence_type} metrics table for {prop} ({gauge}, {dissymmetry_variant})."
        writeline(f"  \\caption{{{caption}}}")
        if not label:
            label = f"table_metric_{prop}_{luminescence_type}_{gauge}_{dissymmetry_variant}"
        writeline(f"  \\label{{tab:{label}}}")
        writeline("\\end{table}\n\n")
    print(f"Latex metric table saved to {output_dir}/{output_filename}")