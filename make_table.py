#!/usr/bin/env python3
"""
Data Extraction Script for Computational Chemistry Outputs

This script extracts absorption and fluorescence data from quantum chemistry output files.
It then prints two LaTeX tables:
 - A comparison table (with multirow entries for molecule names)
 - A metrics summary table comparing computed energies to experimental values
"""

import re
import os
import warnings
import numpy as np
from scipy.stats import pearsonr
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt

# Configuration
MOLECULES_DATA = [
    {
        "name": "Boranil_CH3+RBINOL_H",
        "absorption_wavelength": 396,   # in nm
        "fluorescence_wavelength": 473, # in nm
        "exp_abs_osc": 42,              # 10^3 M-1 cm-1
        "exp_fluo_osc": "<1\%",        
        "exp_gabs": 5.5,                # 10-4
        "exp_glum": np.nan              # 10-4
    },
    {
        "name": "Boranil_I+RBINOL_H",
        "absorption_wavelength": 401,
        "fluorescence_wavelength": 464,
        "exp_abs_osc": 45,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 4.0
    },
    {
        "name": "Boranil_CF3+RBINOL_H",
        "absorption_wavelength": 401,
        "fluorescence_wavelength": 467,
        "exp_abs_osc": 43,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 4.5
    },
    {
        "name": "Boranil_SMe+RBINOL_H",
        "absorption_wavelength": 402,
        "fluorescence_wavelength": 487,
        "exp_abs_osc": 49,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 2.5
    },
    {
        "name": "Boranil_CN+RBINOL_H",
        "absorption_wavelength": 411,
        "fluorescence_wavelength": 467,
        "exp_abs_osc": 46,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 3.5
    },
    {
        "name": "Boranil_NO2+RBINOL_H",
        "absorption_wavelength": 422,
        "fluorescence_wavelength": 472,
        "exp_abs_osc": 34,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 2.0
    },
    {
        "name": "Boranil_NH2+RBINOL_CN",
        "absorption_wavelength": 406,
        "fluorescence_wavelength": 520,
        "exp_abs_osc": 44,
        "exp_fluo_osc": 0.03,
        "exp_gabs": -7.5
    },
    {
        "name": "Boranil_CN+RBINOL_CN",
        "absorption_wavelength": 416,
        "fluorescence_wavelength": 466,
        "exp_abs_osc": 60,
        "exp_fluo_osc": 0.12,
        "exp_gabs": 5.3
    },
    {
        "name": "Boranil_NO2+RBINOL_CN",
        "absorption_wavelength": 426,
        "fluorescence_wavelength": 479,
        "exp_abs_osc": 50.0,
        "exp_fluo_osc": 0.23,
        "exp_gabs": 3.2
    },
    {
        "name": "BODIPY+RBinol_H",
        "absorption_wavelength": 525, # not clearly said on the article
        "fluorescence_wavelength": 570, 
        "exp_abs_osc": 6.0,
        "exp_fluo_osc": 0.47,
        "exp_gabs": 8.4,
        "exp_glum": 7.0
    },
    {
        "name": "Boranil_NH2+F2",
        "absorption_wavelength": 405,
        "fluorescence_wavelength": 528,
        "exp_abs_osc": 48,
        "exp_fluo_osc": 0.02,
        "exp_gabs": 0 
    },
    {
        "name": "Boranil_NO2+F2",
        "absorption_wavelength": 427,
        "fluorescence_wavelength": 474,
        "exp_abs_osc": 66,
        "exp_fluo_osc": 0.60,
        "exp_gabs": 0 
    },
#    {
#        "name": "",
#        "absorption_wavelength":,
#        "fluorescence_wavelength":,
#        "exp_abs_osc":,
#        "exp_fluo_osc":,
#        "exp_gabs": 
#    },
]

# Mapping of original names to display names
MOLECULE_NAME_MAPPING = {
    "Boranil_CH3+RBINOL_H": "CH3+H",
    "Boranil_I+RBINOL_H": "I+H",
    "Boranil_CF3+RBINOL_H": "CF3+H",
    "Boranil_SMe+RBINOL_H": "SMe+H",
    "Boranil_CN+RBINOL_H": "CN+H",
    "Boranil_NO2+RBINOL_H": "NO2+H",
    "Boranil_NH2+RBINOL_CN": "NH2+CN",
    "Boranil_CN+RBINOL_CN": "CN+CN",
    "Boranil_NO2+RBINOL_CN": "NO2+CN",
    "BODIPY+RBinol_H": "BODIPY+H",
    "Boranil_NH2+F2": "NH2+F2",
    "Boranil_NO2+F2": "NO2+F2"
}

# Build experimental data dictionary for each molecule
exp_data = {}
for data in MOLECULES_DATA:
    molecule = data["name"]
    exp_data[molecule] = {
        'ABS': {
            'wavelength': data["absorption_wavelength"],
            'energy': 1240.0 / data["absorption_wavelength"],
            'oscillator': data["exp_abs_osc"],
            'gabs': data["exp_gabs"]
        },
        'FLUO': {
            'wavelength': data["fluorescence_wavelength"],
            'energy': 1240.0 / data["fluorescence_wavelength"],
            'oscillator': data["exp_fluo_osc"]
        }
    }

METHODS = ["B3LYP", "B3LYPtddft", "PBE0", "MO62X", "MO62Xtddft", "CAM-B3LYP", "wB97", "wB97X-D3", "wB97X-D3tddft", "B2PLYP", "CIS", "CISD", "CC2"]

# Set working directory
working_dir = "/home/afrot/Stage2025Tangui"

# Data storage structure: molecule -> method -> calculation type -> {energy, wavelength, oscillator}
dic = {data["name"]: {meth: {'ABS': {}, 'FLUO': {}} for meth in METHODS} for data in MOLECULES_DATA}

def parse_file_orca(molecule: str, method: str, calc_type: str) -> dict or None:
    """
    Parse ORCA output files for electronic transition data values.
    
    Returns a dictionary with formatted values for energy (eV), wavelength (nm), and oscillator strength.
    """
    filename = f"{working_dir}/{molecule}/{molecule}-{calc_type}@{method}/{molecule}-{calc_type}@{method}.out"
    
    if not os.path.exists(filename):
        warnings.warn(f"⚠️ Missing file: {filename}", UserWarning)
        return None
        
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('  0-1A  ->  1-1A'):
                    parts = line.split()
                    if len(parts) < 7:
                        warnings.warn(f"⚠️ Insufficient data in {filename}", UserWarning)
                        return None
                    try:
                        return {
                            'energy': float(parts[3]),
                            'wavelength': float(parts[5]),
                            'oscillator': float(parts[6]),
                        }
                    except (ValueError, IndexError) as e:
                        warnings.warn(f"⚠️ Parsing error in {filename}: {str(e)}", UserWarning)
                        return None
        warnings.warn(f"⚠️ Data line not found in {filename}", UserWarning)
        return None
        
    except Exception as e:
        warnings.warn(f"⚠️ Error reading {filename}: {str(e)}", UserWarning)
        return None

def parse_file_turbomole(molecule: str, method: str, calc_type: str) -> dict or None:
    """
    Parse TURBOMOLE output files for electronic transition data values.

    Returns a dictionary with formatted values for energy (eV), wavelength (nm), and oscillator strength.
    """
    filename = f"{working_dir}/{molecule}/{molecule}-{calc_type}@{method}/ricc2.out"

    if not os.path.exists(filename):
        warnings.warn(f"⚠️ Missing file: {filename}", UserWarning)
        return None

    try:
        with open(filename, 'r') as f:
            energy_ev = None
            oscillator = None
            for line in f:
                # Parse energy from the first relevant frequency line
                pattern = r"\s*\|\s+frequency\s*:\s*[\d.]+\s*a\.u\.\s*([\d.]+)\s*e\.V\.\s*[\d.]+\s*rcm\s+\|\s*"
                match = re.search(pattern, line)
                if match:
                    try:
                        energy_ev = float(match.group(1))
                    except (ValueError, IndexError):
                        pass  # Parsing error handled after loop

                # Parse oscillator strength from the first relevant line
                pattern = r"oscillator strength \(mixed gauge\)\s+:\s+([\d.]+)"
                match = re.search(pattern, line)
                if match:
                    try:
                        oscillator = float(match.group(1))
                    except (ValueError, IndexError):
                        pass  # Parsing error handled after loop

                # Early exit if both values are found
                if energy_ev is not None and oscillator is not None:
                    break

            # Check if both values were successfully parsed
            if energy_ev is None:
                warnings.warn(f"⚠️ Energy not found in {filename}", UserWarning)
                return None
            if oscillator is None:
                warnings.warn(f"⚠️ Oscillator strength not found in {filename}", UserWarning)
                return None
            if energy_ev <= 0:
                warnings.warn(f"⚠️ Non-positive energy value {energy_ev} in {filename}", UserWarning)
                return None

            # Calculate wavelength in nanometers
            wavelength = 1239.84193 / energy_ev

            return {
                'energy': energy_ev,
                'wavelength': wavelength,
                'oscillator': oscillator
            }

    except Exception as e:
        warnings.warn(f"⚠️ Error reading {filename}: {str(e)}", UserWarning)
        return None

def generate_latex_metrics_table(exp_data: dict, dic: dict) -> None:
    """Print LaTeX code for the metrics summary table."""
    print("\\begin{table}[htbp]")
    print("  \\centering")
    print("  \\begin{tabular}{llrrrr}")
    print("    \\toprule")
    print("    Method & Type & MSE & MAE & SD & R$^2$ \\\\")
    print("    \\midrule")
    
    for method in METHODS:
        for calc_type in ['ABS', 'FLUO']:
            calculated = []
            experimental = []
            for data in MOLECULES_DATA:
                molecule = data["name"]
                calc_data = dic[molecule][method][calc_type]
                if calc_data and 'energy' in calc_data:
                    calculated.append(calc_data['energy'])
                    experimental.append(exp_data[molecule][calc_type]['energy'])
            if len(calculated) == 0:
                mse_str = mae_str = r_sq_str = sd_str = 'N/A'
            else:
                errors = [c - e for c, e in zip(calculated, experimental)]
                mse = np.mean(errors) if errors else np.nan
                mae = np.mean(np.abs(errors)) if errors else np.nan
                sd = np.std(errors) if len(errors) > 1 else np.nan
                r_sq = np.nan
                if len(calculated) >= 2:
                    r, _ = pearsonr(experimental, calculated)
                    r_sq = r**2
                mse_str = f"{mse:.2f}" if not np.isnan(mse) else 'N/A'
                mae_str = f"{mae:.2f}" if not np.isnan(mae) else 'N/A'
                sd_str = f"{sd:.2f}" if not np.isnan(sd) else 'N/A'
                r_sq_str = f"{r_sq:.2f}" if not np.isnan(r_sq) else 'N/A'
            print(f"    {method} & {calc_type} & {mse_str} & {mae_str} & {sd_str} & {r_sq_str} \\\\")
    print("    \\bottomrule")
    print("  \\end{tabular}")
    print("  \\caption{\\centering Metrics Summary Comparing Computational Methods to Experimental Data.}")
    print("  \\label{tab:metrics}")
    print("\\end{table}")

def generate_latex_tables():
    """Generate LaTeX tables split into chunks of max {max_molecule_per_table} molecules"""
    max_molecule_per_table = 4
    chunks = [MOLECULES_DATA[i:i+max_molecule_per_table] for i in range(0, len(MOLECULES_DATA), max_molecule_per_table)]

    for table_num, chunk in enumerate(chunks, 1):
        print(f"\\begin{{table}}[htbp]")
        print("  \\centering")
        print("  \\scriptsize")
        print("  \\begin{tabular}{llcccccccc}")
        print("    \\toprule")
        print("    Molecule & Method & $\\lambda_{\\text{Abs}}$ (nm)& E$_{\\text{Abs}}$ (eV) & fosc$_{\\text{Abs}}$/$\\epsilon$ & $\\lambda_{\\text{Fluo}}$ (nm)& E$_{\\text{Fluo}}$ (eV) & fosc$_{\\text{Fluo}}$/$\\Phi_\\text{f}$\\\\")
        print("    \\midrule")

        for data in chunk:
            molecule = data["name"]
            display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
            exp_abs = exp_data[molecule]['ABS']
            exp_fluo = exp_data[molecule]['FLUO']

            # Experimental row
            exp_row = (
                "Exp",
                f"{exp_abs['wavelength']:.0f}",
                f"{exp_abs['energy']:.2f}",
                f"{exp_abs['oscillator']}",
                f"{exp_fluo['wavelength']:.0f}",
                f"{exp_fluo['energy']:.2f}",
                f"{exp_fluo['oscillator']}"
            )
            print(f"    \\multirow{{{len(METHODS)+1}}}{{*}}{{{display_name}}} & " + " & ".join(exp_row) + " \\\\\\\\")

            # Computed rows
            for method in METHODS:
                abs_data = dic[molecule][method]['ABS']
                fluo_data = dic[molecule][method]['FLUO']

                # Format data
                abs_values = [
                    f"{abs_data.get('wavelength', 'N/A'):.0f}" if isinstance(abs_data.get('wavelength'), float) else 'N/A',
                    f"{abs_data.get('energy', 'N/A'):.2f}" if isinstance(abs_data.get('energy'), float) else 'N/A',
                    f"{abs_data.get('oscillator', 'N/A'):.2f}" if isinstance(abs_data.get('oscillator'), float) else 'N/A'
                ]

                fluo_values = [
                    f"{fluo_data.get('wavelength', 'N/A'):.0f}" if isinstance(fluo_data.get('wavelength'), float) else 'N/A',
                    f"{fluo_data.get('energy', 'N/A'):.2f}" if isinstance(fluo_data.get('energy'), float) else 'N/A',
                    f"{fluo_data.get('oscillator', 'N/A'):.2f}" if isinstance(fluo_data.get('oscillator'), float) else 'N/A'
                ]

                print(f"     & {method} & {' & '.join(abs_values)} & {' & '.join(fluo_values)} \\\\")

            print("    \\midrule")

        print("    \\bottomrule")
        print("  \\end{tabular}")
        print(f"  \\caption{{Benchmark of TD-DFT functionals (Part {table_num})}}")
        print(f"  \\label{{tab:comparison{table_num}}}")
        print("\\end{table}\n\n")

def generate_comparison_plots():
    """Generate comparison plots with regression analysis"""
    for method in METHODS:
        plt.figure(figsize=(8, 6))
        abs_x, abs_y, abs_labels = [], [], []
        fluo_x, fluo_y, fluo_labels = [], [], []
        
        for molecule in exp_data:
            display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)

            # Absorption data
            comp_abs = dic[molecule][method]['ABS'].get('energy')
            exp_abs = exp_data[molecule]['ABS'].get('energy')
            if comp_abs and exp_abs and not np.isnan([comp_abs, exp_abs]).any():
                abs_x.append(exp_abs)
                abs_y.append(comp_abs)
                abs_labels.append(display_name)
            
            # Fluorescence data
            comp_fluo = dic[molecule][method]['FLUO'].get('energy')
            exp_fluo = exp_data[molecule]['FLUO'].get('energy')
            if comp_fluo and exp_fluo and not np.isnan([comp_fluo, exp_fluo]).any():
                fluo_x.append(exp_fluo)
                fluo_y.append(comp_fluo)
                fluo_labels.append(display_name)
        
        # Only plot if there's data
        if abs_x or fluo_x:
            # Create plots
            if abs_x:
                plt.scatter(abs_x, abs_y, c='blue', label='Absorption')
#                for i, label in enumerate(abs_labels):
#                    plt.text(abs_x[i], abs_y[i], label,
#                             fontsize=8, color='blue',
#                             #ha='right', va='bottom', alpha=0.7
#                             )
            if fluo_x:
                plt.scatter(fluo_x, fluo_y, c='red', label='Fluorescence')
#                for i, label in enumerate(fluo_labels):
#                    plt.text(fluo_x[i], fluo_y[i], label,
#                             fontsize=8, color='red',
#                             #ha='left', va='top', alpha=0.7
#                             )

            # Set equal axis limits
            all_x = abs_x + fluo_x
            all_y = abs_y + fluo_y
            min_val = min(min(all_x), min(all_y))
            max_val = max(max(all_x), max(all_y))
            padding = 0.1 * (max_val - min_val)
            axis_min = min_val - padding
            axis_max = max_val + padding
            plt.xlim(axis_min, axis_max)
            plt.ylim(axis_min, axis_max)

            # Add a diagonal line for reference (y = x)
            plt.plot([axis_min, axis_max], [axis_min, axis_max],
                     color='gray', linestyle=':', alpha=0.5)

            plt.title(f"Experimental vs Computed Energies ({method})")
            plt.xlabel("Experimental Energy (eV)")
            plt.ylabel("Computed Energy (eV)")
            plt.legend()
            plt.tight_layout()
            plt.savefig(f"plot_comparison/{method}_comparison.pdf")
            plt.close()
        else:
            print(f"No valid data for {method}, skipping plot")

def main():
    """Main function to coordinate data collection and LaTeX table generation."""
    # Collect computational data
    for data in MOLECULES_DATA:
        molecule = data["name"]
        for method in METHODS:
            if method != "CC2":
                abs_result = parse_file_orca(molecule, method, 'ABS')
                fluo_result = parse_file_orca(molecule, method, 'FLUO')
            else:
                abs_result = parse_file_turbomole(molecule, method, 'ABS')
                fluo_result = parse_file_turbomole(molecule, method, 'FLUO')

            if abs_result:
                dic[molecule][method]['ABS'] = abs_result
            if fluo_result:
                dic[molecule][method]['FLUO'] = fluo_result
    
    # Print LaTeX tables
    generate_latex_tables()
    print("\n\n")  # Separate the two tables with some newlines
    generate_latex_metrics_table(exp_data, dic)
    generate_comparison_plots()
    print("")
    print(f"Plots done")

if __name__ == "__main__":
    main()

