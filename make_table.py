"""
Data Extraction Script for Computational Chemistry Outputs

This script extracts absorption and fluorescence data from quantum chemistry output files.
It then prints two LaTeX tables:
 - A comparison table (with multirow entries for molecule names)
 - A metrics summary table comparing computed energies to experimental values
"""

import os
import warnings
import numpy as np
from scipy.stats import pearsonr

# Configuration
MOLECULES_DATA = [
    {
        "name": "Boranil_CH3+RBINOL_H",
        "absorption_wavelength": 396,
        "fluorescence_wavelength": 473,
        "exp_abs_osc": 42,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 5.5
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
        "exp_gabs": np.nan
    },
    {
        "name": "Boranil_NO2+RBINOL_CN",
        "absorption_wavelength": 426,
        "fluorescence_wavelength": 479,
        "exp_abs_osc": 50,
        "exp_fluo_osc": 0.23,
        "exp_gabs": 3.2
    }
]

exp_data = {}

# Build experimental data dictionary for each molecule
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

METHODS = ["B3LYP", "PBE0", "MO62X", "CAM-B3LYP", "wB97", "wB97X-D3", "B2PLYP", "CISD"]

# Set working directory
working_dir = "/home/afrot/Stage2025Tangui"

# Data storage structure: molecule -> method -> calculation type -> {energy, wavelength, oscillator}
dic = {data["name"]: {meth: {'ABS': {}, 'FLUO': {}} for meth in METHODS} for data in MOLECULES_DATA}

def parse_file(molecule: str, method: str, calc_type: str) -> dict or None:
    """
    Parse quantum chemistry output files for specific data values.
    
    Returns a dictionary with formatted values for energy, wavelength, and oscillator strength.
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

def generate_latex_table(exp_data: dict) -> None:
    """Print LaTeX code for the main comparison table with computed and experimental values."""
    print("\\begin{table}[htbp]")
    print("  \\centering")
    print("  \\scriptsize")
    print("  \\begin{tabular}{llcccccccc}")
    print("    \\toprule")
    print("    Molecule & Method & $\\lambda_{\\text{Abs}}$ (nm)& E$_{\\text{Abs}}$ (eV) & fosc$_{\\text{Abs}}$/$\\epsilon$ & $\\lambda_{\\text{Fluo}}$ (nm)& E$_{\\text{Fluo}}$ (eV) & fosc$_{\\text{Fluo}}$/$\\Phi_\\text{f}$\\\\")
    print("    \\midrule")
    
    for data in MOLECULES_DATA:
        molecule = data["name"]
        # --- Experimental row ---
        exp_abs = exp_data[molecule]['ABS']
        exp_fluo = exp_data[molecule]['FLUO']
        exp_row = (
            "Exp",
            f"{exp_abs['wavelength']:.0f}",
            f"{exp_abs['energy']:.2f}",
            f"{exp_abs['oscillator']}",
            f"{exp_fluo['wavelength']:.0f}",
            f"{exp_fluo['energy']:.2f}",
            f"{exp_fluo['oscillator']}"
        )
        
        print(f"    \\multirow{{{len(METHODS) + 2}}}{{*}}{{{molecule}}}" + " & " + " & ".join(exp_row) + " \\\\\\\\")

        # --- Computed rows for each method ---
        for method in METHODS:
            abs_data = dic[molecule][method]['ABS']
            fluo_data = dic[molecule][method]['FLUO']
            
            abs_values = [abs_data.get('wavelength', 'N/A'),
                          abs_data.get('energy', 'N/A'),
                          abs_data.get('oscillator', 'N/A')] if abs_data else ['N/A'] * 3
            fluo_values = [fluo_data.get('wavelength', 'N/A'),
                           fluo_data.get('energy', 'N/A'),
                           fluo_data.get('oscillator', 'N/A')] if fluo_data else ['N/A'] * 3
            
            abs_lam_str = f"{abs_values[0]:.0f}" if isinstance(abs_values[0], float) else f"{abs_values[0]}"
            abs_en_str  = f"{abs_values[1]:.2f}" if isinstance(abs_values[1], float) else f"{abs_values[1]}"
            abs_osc_str = f"{abs_values[2]:.2f}" if isinstance(abs_values[2], float) else f"{abs_values[2]}"
            
            fluo_lam_str = f"{fluo_values[0]:.0f}" if isinstance(fluo_values[0], float) else f"{fluo_values[0]}"
            fluo_en_str  = f"{fluo_values[1]:.2f}" if isinstance(fluo_values[1], float) else f"{fluo_values[1]}"
            fluo_osc_str = f"{fluo_values[2]:.2f}" if isinstance(fluo_values[2], float) else f"{fluo_values[2]}"
            
            print(f"     & {method} & {abs_lam_str} & {abs_en_str} & {abs_osc_str} & {fluo_lam_str} & {fluo_en_str} & {fluo_osc_str} \\\\")

        print("    \\midrule")
    print("    \\bottomrule")
    print("  \\end{tabular}")
    print("  \\caption{Benshmark of several TD-DFT functionnals.}")
    print("  \\label{tab:comparison}")
    print("\\end{table}")

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

def main():
    """Main function to coordinate data collection and LaTeX table generation."""
    # Collect computational data
    for data in MOLECULES_DATA:
        molecule = data["name"]
        for method in METHODS:
            abs_result = parse_file(molecule, method, 'ABS')
            if abs_result:
                dic[molecule][method]['ABS'] = abs_result
            fluo_result = parse_file(molecule, method, 'FLUO')
            if fluo_result:
                dic[molecule][method]['FLUO'] = fluo_result
    
    # Print LaTeX tables
    generate_latex_table(exp_data)
    print("\n\n")  # Separate the two tables with some newlines
    generate_latex_metrics_table(exp_data, dic)

if __name__ == "__main__":
    main()

