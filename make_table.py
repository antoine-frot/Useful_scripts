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
warnings.simplefilter("always")
warnings.formatwarning = lambda msg, cat, fname, lno, line: f"{msg}\n"
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
        "exp_glum": np.nan,              # 10-4
        "display": True
    },
    {
        "name": "Boranil_I+RBINOL_H",
        "absorption_wavelength": 401,
        "fluorescence_wavelength": 464,
        "exp_abs_osc": 45,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 4.0,
        "display": True
    },
    {
        "name": "Boranil_CF3+RBINOL_H",
        "absorption_wavelength": 401,
        "fluorescence_wavelength": 467,
        "exp_abs_osc": 43,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 4.5,
        "display": True
    },
    {
        "name": "Boranil_SMe+RBINOL_H",
        "absorption_wavelength": 402,
        "fluorescence_wavelength": 487,
        "exp_abs_osc": 49,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 2.5,
        "display": True
    },
    {
        "name": "Boranil_CN+RBINOL_H",
        "absorption_wavelength": 411,
        "fluorescence_wavelength": 467,
        "exp_abs_osc": 46,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 3.5,
        "display": True
    },
    {
        "name": "Boranil_NO2+RBINOL_H",
        "absorption_wavelength": 422,
        "fluorescence_wavelength": 472,
        "exp_abs_osc": 34,
        "exp_fluo_osc": "<1\%",
        "exp_gabs": 2.0,
        "display": True
    },
    {
        "name": "Boranil_NH2+RBINOL_CN",
        "absorption_wavelength": 406,
        "fluorescence_wavelength": 520,
        "exp_abs_osc": 44,
        "exp_fluo_osc": 0.03,
        "exp_gabs": -7.5,
        "display": True
    },
    {
        "name": "Boranil_I+RBINOL_CN",
        "absorption_wavelength": 426,
        "fluorescence_wavelength": 475,
        "exp_abs_osc": 53.5,
        "exp_fluo_osc": 0.14,
        "exp_gabs": 6.4,
        "display": True
    },
    {
        "name": "Boranil_CN+RBINOL_CN",
        "absorption_wavelength": 416,
        "fluorescence_wavelength": 466,
        "exp_abs_osc": 60,
        "exp_fluo_osc": 0.12,
        "exp_gabs": 5.3,
        "display": True
    },
    {
        "name": "Boranil_NO2+RBINOL_CN",
        "absorption_wavelength": 426,
        "fluorescence_wavelength": 479,
        "exp_abs_osc": 49.5,
        "exp_fluo_osc": 0.23,
        "exp_gabs": 3.2,
        "display": True
    },
    {
        "name": "Boranil_NH2+RBINOL_CN",
        "absorption_wavelength": 405,
        "fluorescence_wavelength": 518,
        "exp_abs_osc": 44.0,
        "exp_fluo_osc": 0.03,
        "exp_gabs": 7.5,
        "display": True
    },
    {
        "name": "BODIPY+RBinol_H",
        "absorption_wavelength": 525, # not clearly said on the article
        "fluorescence_wavelength": 570, 
        "exp_abs_osc": 6.0,
        "exp_fluo_osc": 0.47,
        "exp_gabs": 8.4,
        "exp_glum": 7.0,
        "display": False
    },
    {
        "name": "Boranil_NH2+F2",
        "absorption_wavelength": 405,
        "fluorescence_wavelength": 528,
        "exp_abs_osc": 48,
        "exp_fluo_osc": 0.02,
        "exp_gabs": 0,
        "display": False
    },
    {
        "name": "Boranil_NO2+F2",
        "absorption_wavelength": 427,
        "fluorescence_wavelength": 474,
        "exp_abs_osc": 66,
        "exp_fluo_osc": 0.60,
        "exp_gabs": 0, 
        "display": False
    },
#    {
#        "name": "",
#        "absorption_wavelength":,
#        "fluorescence_wavelength":,
#        "exp_abs_osc":,
#        "exp_fluo_osc":,
#        "exp_gabs":, 
#        "display": False
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
        },
        'display': data["display"],
    }

METHODS = ["OPTB3LYP", "B3LYPtddft", "PBE0", "MO62X", "MO62Xtddft", "CAM-B3LYP", "wB97", "wB97X-D3", "wB97X-D3tddft", "B2PLYP", "B2PLYPtddft", "CIS", "CISD", "CC2"]

# Set working directory
working_dir = "/home/afrot/Stage2025Tangui"

# Data storage structure: molecule -> method -> calculation type -> {energy, wavelength, oscillator}
dic = {data["name"]: {meth: {'ABS': {}, 'FLUO': {}} for meth in METHODS} for data in MOLECULES_DATA}

import os
import re
import warnings

def parse_file_orca(molecule: str, method: str, calc_type: str, solvant_correction: float) -> dict:
    """
    Parse ORCA output files for electronic transition data values.

    Returns a dictionary with formatted values for energy (eV), wavelength (nm), oscillator strength,
    and transition dipole moments.
    """
    filename = f"{working_dir}/{molecule}/{molecule}-{calc_type}@{method}/{molecule}-{calc_type}@{method}.out"

    if not os.path.exists(filename):
        warnings.warn(f"⚠️ Missing file: {molecule}-{calc_type}@{method}", UserWarning)
        return {}

    data = {
        'energy': None,
        'wavelength': None,
        'oscillator_length': None,
        'D2': None,
        'DX': None,
        'DY': None,
        'DZ': None,
        'oscillator_velocity': None,
        'P2': None,
        'PX': None,
        'PY': None,
        'PZ': None,
        'rotator_length': None,
        'MX': None,
        'MY': None,
        'MZ': None,
        'rotator_velocity': None,
    }

    try:
        with open(filename, 'r') as f:
            pattern = (
                r'0-1\S+\s+->\s+1-1\S+\s+'
                r'\s+(?P<energy_eV>[-+]?\d+\.\d+)'
                r'\s+(?P<energy_rcm>[-+]?\d+\.\d+)'
                r'\s+(?P<wavelength>[-+]?\d+\.\d+)'
                r'\s+(?P<strength>[-+]?\d+\.\d+)'
                r'\s+(?P<transition_dipole1>[-+]?\d+\.\d+)'
                r'\s+(?P<transition_dipole2>[-+]?\d+\.\d+)'
                r'\s+(?P<transition_dipole3>[-+]?\d+\.\d+)'
                r'\s+(?P<transition_dipole4>[-+]?\d+\.\d+)?'
            )
            counter = 0
            for line in f:
                match = re.search(pattern, line)
                if match:
                    try:
                        if counter == 0:
                            if method in ("CISD", "CIS"):
                                data['energy'] = float(match.group('energy_eV')) + solvant_correction
                                data['wavelength'] = 1239.84193 / data['energy']
                            else:
                                data['energy'] = float(match.group('energy_eV'))
                                data['wavelength'] = float(match.group('wavelength'))
                            data['oscillator_length'] = float(match.group('strength'))
                            data['D2'] = float(match.group('transition_dipole1'))
                            data['DX'] = float(match.group('transition_dipole2'))
                            data['DY'] = float(match.group('transition_dipole3'))
                            data['DZ'] = float(match.group('transition_dipole4'))
                        elif counter == 1:
                            data['oscillator_velocity'] = float(match.group('strength'))
                            data['P2'] = float(match.group('transition_dipole1'))
                            data['PX'] = float(match.group('transition_dipole2'))
                            data['PY'] = float(match.group('transition_dipole3'))
                            data['PZ'] = float(match.group('transition_dipole4'))
                        elif counter == 2:
                            data['rotator_length'] = float(match.group('strength'))
                            data['MX'] = float(match.group('transition_dipole1'))
                            data['MY'] = float(match.group('transition_dipole2'))
                            data['MZ'] = float(match.group('transition_dipole3'))
                        elif counter == 3:
                            data['rotator_velocity'] = float(match.group('strength'))
                        counter += 1
                    except (ValueError, IndexError) as e:
                        warnings.warn(f"⚠️ Parsing error in {filename}: {str(e)}", UserWarning)
                        return {}
        return data
    except Exception as e:
        warnings.warn(f"⚠️ Error reading file {filename}: {str(e)}", UserWarning)
        return {}

def parse_file_turbomole(molecule: str, method: str, calc_type: str, solvant_correction: float) -> dict:
    """
    Parse TURBOMOLE output files for electronic transition data values.

    Returns a dictionary with formatted values for energy (eV), wavelength (nm), oscillator strength,
    and transition dipole moments.
    """
    filename = f"{working_dir}/{molecule}/{molecule}-{calc_type}@{method}/ricc2.out"

    if not os.path.exists(filename):
        warnings.warn(f"⚠️ Missing file: {filename}", UserWarning)
        return None

    data = {
        'energy': None,
        'wavelength': None,
        'oscillator_length': None,
        'DX': None,
        'DY': None,
        'DZ': None,
        'oscillator_velocity': None,
        'PX': None,
        'PY': None,
        'PZ': None,
        'rotator_length': None,
        'MX': None,
        'MY': None,
        'MZ': None,
        'rotator_velocity': None,
    }

    patterns = {
        'energy': r'(\d+\.\d+)\s+e\.V\.',
        'DX': r'xdiplen\s+\|\s+\S+\s+\|\s+(\S+)',
        'DY': r'ydiplen\s+\|\s+\S+\s+\|\s+(\S+)',
        'DZ': r'zdiplen\s+\|\s+\S+\s+\|\s+(\S+)',
        'PX': r'xdipvel\s+\|\s+\S+\s+\|\s+(\S+)',
        'PY': r'ydipvel\s+\|\s+\S+\s+\|\s+(\S+)',
        'PZ': r'zdipvel\s+\|\s+\S+\s+\|\s+(\S+)',
        'MX': r'xangmom\s+\|\s+\S+\s+\|\s+(\S+)',
        'MY': r'yangmom\s+\|\s+\S+\s+\|\s+(\S+)',
        'MZ': r'zangmom\s+\|\s+\S+\s+\|\s+(\S+)',
        'oscillator_length': r'oscillator strength \(length gauge\)\s+:\s+(\S+)',
        'oscillator_velocity': r'oscillator strength \(velocity gauge\)\s+:\s+(\S+)',
        'rotator_length': r'Rotator strength \(length gauge\)\s+:\s+(\S+)\s+10\^\(-40\)\*erg\*cm\^3',
        'rotator_velocity': r'Rotator strength \(velocity gauge\)\s+:\s+(\S+)\s+10\^\(-40\)\*erg\*cm\^3',
    }

    try:
        with open(filename, 'r') as f:
            for line in f:
                for key, pattern in patterns.items():
                    match = re.search(pattern, line)
                    if match:
                        try:
                            if key == 'energy':
                                data[key] = float(match.group(1)) + solvant_correction
                                data['wavelength'] = 1239.84193 / data[key]
                            else:
                                data[key] = float(match.group(1))

                        except (ValueError, IndexError) as e:
                            warnings.warn(f"⚠️ Parsing error in {filename}: {str(e)}", UserWarning)
                            return {}

                if all(value is not None for value in data.values()):
                    return data

    except Exception as e:
        warnings.warn(f"⚠️ Error reading file {filename}: {str(e)}", UserWarning)
        return {}

    return data

def get_solvatation_correction(molecule: str, method: str, calc_type: str, warnings):
    solv = parse_file_orca(molecule, method, calc_type, 0)
    no_solv = parse_file_orca(molecule, f"{method}_nosolv", calc_type, 0)
    if solv['energy'] and no_solv['energy']:
        return solv['energy'] - no_solv['energy']
    else:
        warnings.append(f"Warning: No solvatation correction for {molecule} in {calc_type}")
        return 0
    
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
                    f"{abs_data.get('oscillator_length', 'N/A'):.2f}" if isinstance(abs_data.get('oscillator_length'), float) else 'N/A'
                ]

                fluo_values = [
                    f"{fluo_data.get('wavelength', 'N/A'):.0f}" if isinstance(fluo_data.get('wavelength'), float) else 'N/A',
                    f"{fluo_data.get('energy', 'N/A'):.2f}" if isinstance(fluo_data.get('energy'), float) else 'N/A',
                    f"{fluo_data.get('oscillator_length', 'N/A'):.2f}" if isinstance(fluo_data.get('oscillator_length'), float) else 'N/A'
                ]

                print(f"     & {method} & {' & '.join(abs_values)} & {' & '.join(fluo_values)} \\\\")

            print("    \\midrule")

        print("    \\bottomrule")
        print("  \\end{tabular}")
        print(f"  \\caption{{Benchmark of TD-DFT functionals (Part {table_num})}}")
        print(f"  \\label{{tab:comparison{table_num}}}")
        print("\\end{table}\n\n")

def generate_CD():
    """
    Calculate CD parameters for all molecules and methods:
    - gabs/glum (both length and velocity gauge) using two different methods
    - Vector norms for magnetic and electric dipole moments
    - Angles between magnetic and electric dipole moments
    """
    for data in MOLECULES_DATA:
        molecule = data["name"]
        for method in METHODS:
            # Process absorption data
            abs_data = dic[molecule][method]['ABS']
            if abs_data and 'rotator_length' in abs_data and 'oscillator_length' in abs_data:
                # Calculate g-factors (both gauges) - method 1: 4R/D
                if abs_data.get('oscillator_length') and abs_data.get('oscillator_length', 0) != 0:
                    abs_data['gabs_length'] = 4 * abs_data.get('rotator_length', 0) / abs_data.get('oscillator_length') * 1e4
                else:
                    abs_data['gabs_length'] = np.nan
                    
                if abs_data.get('oscillator_velocity') and abs_data.get('oscillator_velocity', 0) != 0:
                    abs_data['gabs_velocity'] = 4 * abs_data.get('rotator_velocity', 0) / abs_data.get('oscillator_velocity') * 1e4
                else:
                    abs_data['gabs_velocity'] = np.nan
                
                # Calculate vector norms - check for None values before computing
                if all(abs_data.get(key) is not None for key in ['MX', 'MY', 'MZ']):
                    abs_data['M_norm'] = np.sqrt(abs_data['MX']**2 + abs_data['MY']**2 + abs_data['MZ']**2)
                else:
                    abs_data['M_norm'] = np.nan
                    
                if all(abs_data.get(key) is not None for key in ['DX', 'DY', 'DZ']):
                    abs_data['D_norm'] = np.sqrt(abs_data['DX']**2 + abs_data['DY']**2 + abs_data['DZ']**2)
                else:
                    abs_data['D_norm'] = np.nan
                    
                if all(abs_data.get(key) is not None for key in ['PX', 'PY', 'PZ']):
                    abs_data['P_norm'] = np.sqrt(abs_data['PX']**2 + abs_data['PY']**2 + abs_data['PZ']**2)
                else:
                    abs_data['P_norm'] = np.nan
                
                # Calculate angles (in degrees) - check all values exist and norms are positive
                if (all(abs_data.get(key) is not None for key in ['MX', 'MY', 'MZ', 'DX', 'DY', 'DZ']) 
                        and abs_data.get('M_norm', 0) > 0 and abs_data.get('D_norm', 0) > 0):
                    dot_product = abs_data['MX']*abs_data['DX'] + abs_data['MY']*abs_data['DY'] + abs_data['MZ']*abs_data['DZ']
                    cos_angle = dot_product / (abs_data['M_norm'] * abs_data['D_norm'])
                    # Ensure cos_angle is in valid range [-1, 1] due to potential floating point errors
                    cos_angle = max(min(cos_angle, 1.0), -1.0)
                    abs_data['angle_MD'] = np.degrees(np.arccos(cos_angle))
                    abs_data['cos_MD'] = cos_angle
                    
                    # Calculate g-factor using method 2: 4 × |m| cos θ / |μ|
                    abs_data['gabs_length_alt'] = 4 * abs_data['M_norm'] * cos_angle / abs_data['D_norm'] * 1e4
                else:
                    abs_data['angle_MD'] = np.nan
                    abs_data['cos_MD'] = np.nan
                    abs_data['gabs_length_alt'] = np.nan
                    
                if (all(abs_data.get(key) is not None for key in ['MX', 'MY', 'MZ', 'PX', 'PY', 'PZ'])
                        and abs_data.get('M_norm', 0) > 0 and abs_data.get('P_norm', 0) > 0):
                    dot_product = abs_data['MX']*abs_data['PX'] + abs_data['MY']*abs_data['PY'] + abs_data['MZ']*abs_data['PZ']
                    cos_angle = dot_product / (abs_data['M_norm'] * abs_data['P_norm'])
                    cos_angle = max(min(cos_angle, 1.0), -1.0)
                    abs_data['angle_MP'] = np.degrees(np.arccos(cos_angle))
                    abs_data['cos_MP'] = cos_angle
                    
                    # Calculate g-factor using method 2: 4 × |m| cos θ / |μ|
                    abs_data['gabs_velocity_alt'] = 4 * abs_data['M_norm'] * cos_angle / abs_data['P_norm'] * 1e4
                else:
                    abs_data['angle_MP'] = np.nan
                    abs_data['cos_MP'] = np.nan
                    abs_data['gabs_velocity_alt'] = np.nan
            
            # Process fluorescence data
            fluo_data = dic[molecule][method]['FLUO']
            if fluo_data and 'rotator_length' in fluo_data and 'oscillator_length' in fluo_data:
                # Calculate g-factors (both gauges) - method 1: 4R/D
                if fluo_data.get('oscillator_length') and fluo_data.get('oscillator_length', 0) != 0:
                    fluo_data['glum_length'] = 4 * fluo_data.get('rotator_length', 0) / fluo_data.get('oscillator_length') * 1e4
                else:
                    fluo_data['glum_length'] = np.nan
                    
                if fluo_data.get('oscillator_velocity') and fluo_data.get('oscillator_velocity', 0) != 0:
                    fluo_data['glum_velocity'] = 4 * fluo_data.get('rotator_velocity', 0) / fluo_data.get('oscillator_velocity') * 1e4
                else:
                    fluo_data['glum_velocity'] = np.nan
                
                # Calculate vector norms - check for None values before computing
                if all(fluo_data.get(key) is not None for key in ['MX', 'MY', 'MZ']):
                    fluo_data['M_norm'] = np.sqrt(fluo_data['MX']**2 + fluo_data['MY']**2 + fluo_data['MZ']**2)
                else:
                    fluo_data['M_norm'] = np.nan
                    
                if all(fluo_data.get(key) is not None for key in ['DX', 'DY', 'DZ']):
                    fluo_data['D_norm'] = np.sqrt(fluo_data['DX']**2 + fluo_data['DY']**2 + fluo_data['DZ']**2)
                else:
                    fluo_data['D_norm'] = np.nan
                    
                if all(fluo_data.get(key) is not None for key in ['PX', 'PY', 'PZ']):
                    fluo_data['P_norm'] = np.sqrt(fluo_data['PX']**2 + fluo_data['PY']**2 + fluo_data['PZ']**2)
                else:
                    fluo_data['P_norm'] = np.nan
                
                # Calculate angles (in degrees) - check all values exist and norms are positive
                if (all(fluo_data.get(key) is not None for key in ['MX', 'MY', 'MZ', 'DX', 'DY', 'DZ']) 
                        and fluo_data.get('M_norm', 0) > 0 and fluo_data.get('D_norm', 0) > 0):
                    dot_product = fluo_data['MX']*fluo_data['DX'] + fluo_data['MY']*fluo_data['DY'] + fluo_data['MZ']*fluo_data['DZ']
                    cos_angle = dot_product / (fluo_data['M_norm'] * fluo_data['D_norm'])
                    cos_angle = max(min(cos_angle, 1.0), -1.0)
                    fluo_data['angle_MD'] = np.degrees(np.arccos(cos_angle))
                    fluo_data['cos_MD'] = cos_angle
                    
                    # Calculate g-factor using method 2: 4 × |m| cos θ / |μ|
                    fluo_data['glum_length_alt'] = 4 * fluo_data['M_norm'] * cos_angle / fluo_data['D_norm'] * 1e4
                else:
                    fluo_data['angle_MD'] = np.nan
                    fluo_data['cos_MD'] = np.nan
                    fluo_data['glum_length_alt'] = np.nan
                    
                if (all(fluo_data.get(key) is not None for key in ['MX', 'MY', 'MZ', 'PX', 'PY', 'PZ'])
                        and fluo_data.get('M_norm', 0) > 0 and fluo_data.get('P_norm', 0) > 0):
                    dot_product = fluo_data['MX']*fluo_data['PX'] + fluo_data['MY']*fluo_data['PY'] + fluo_data['MZ']*fluo_data['PZ']
                    cos_angle = dot_product / (fluo_data['M_norm'] * fluo_data['P_norm'])
                    cos_angle = max(min(cos_angle, 1.0), -1.0)
                    fluo_data['angle_MP'] = np.degrees(np.arccos(cos_angle))
                    fluo_data['cos_MP'] = cos_angle
                    
                    # Calculate g-factor using method 2: 4 × |m| cos θ / |μ|
                    fluo_data['glum_velocity_alt'] = 4 * fluo_data['M_norm'] * cos_angle / fluo_data['P_norm'] * 1e4
                else:
                    fluo_data['angle_MP'] = np.nan
                    fluo_data['cos_MP'] = np.nan
                    fluo_data['glum_velocity_alt'] = np.nan


def generate_latex_tables_CD():
    """Generate LaTeX tables with CD data split into chunks of max {max_molecule_per_table} molecules"""
    max_molecule_per_table = 4
    chunks = [MOLECULES_DATA[i:i+max_molecule_per_table] for i in range(0, len(MOLECULES_DATA), max_molecule_per_table)]

    for table_num, chunk in enumerate(chunks, 1):
        print(f"\\begin{{table}}[htbp]")
        print("  \\centering")
        print("  \\scriptsize")
        print("  \\begin{tabular}{llcccccccc}")
        print("    \\toprule")
        print("    Molecule & Method & $g_{\\text{abs}}$ ($10^{-4}$)& $g_{\\text{abs}}^{\\text{vel}}$ ($10^{-4}$) & $\\theta_{\\text{MD}}$ ($^\\circ$) & $\\theta_{\\text{MP}}$ ($^\\circ$) & $g_{\\text{lum}}$ ($10^{-4}$)& $g_{\\text{lum}}^{\\text{vel}}$ ($10^{-4}$) & $\\theta_{\\text{MD}}$ ($^\\circ$) & $\\theta_{\\text{MP}}$ ($^\\circ$)\\\\")
        print("    \\midrule")

        for data in chunk:
            molecule = data["name"]
            if not molecule in exp_data or not exp_data[molecule]['display']:
                continue
                
            display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
            exp_gabs = exp_data[molecule]['ABS'].get('gabs', np.nan)
            exp_glum = data.get("exp_glum", np.nan)  # Try to get exp_glum from original data

            # Experimental row
            exp_row = [
                "Exp",
                f"{exp_gabs:.1f}" if not np.isnan(exp_gabs) else "N/A",
                "N/A",  # No velocity gauge for experimental
                "N/A",  # No angle data for experimental
                "N/A",
                f"{exp_glum:.1f}" if not np.isnan(exp_glum) else "N/A",
                "N/A",  # No velocity gauge for experimental
                "N/A",  # No angle data for experimental
                "N/A"
            ]
            print(f"    \\multirow{{{len(METHODS)+1}}}{{*}}{{{display_name}}} & " + " & ".join(exp_row) + " \\\\\\\\")

            # Computed rows
            for method in METHODS:
                abs_data = dic[molecule][method]['ABS']
                fluo_data = dic[molecule][method]['FLUO']

                # Format absorption data
                gabs_length = abs_data.get('gabs_length', np.nan)
                gabs_velocity = abs_data.get('gabs_velocity', np.nan)
                angle_md_abs = abs_data.get('angle_MD', np.nan)
                angle_mp_abs = abs_data.get('angle_MP', np.nan)
                
                abs_values = [
                    f"{gabs_length:.1f}" if not np.isnan(gabs_length) else "N/A",
                    f"{gabs_velocity:.1f}" if not np.isnan(gabs_velocity) else "N/A",
                    f"{angle_md_abs:.1f}" if not np.isnan(angle_md_abs) else "N/A",
                    f"{angle_mp_abs:.1f}" if not np.isnan(angle_mp_abs) else "N/A"
                ]

                # Format fluorescence data
                glum_length = fluo_data.get('glum_length', np.nan)
                glum_velocity = fluo_data.get('glum_velocity', np.nan)
                angle_md_fluo = fluo_data.get('angle_MD', np.nan)
                angle_mp_fluo = fluo_data.get('angle_MP', np.nan)
                
                fluo_values = [
                    f"{glum_length:.1f}" if not np.isnan(glum_length) else "N/A",
                    f"{glum_velocity:.1f}" if not np.isnan(glum_velocity) else "N/A",
                    f"{angle_md_fluo:.1f}" if not np.isnan(angle_md_fluo) else "N/A",
                    f"{angle_mp_fluo:.1f}" if not np.isnan(angle_mp_fluo) else "N/A"
                ]

                print(f"     & {method} & {' & '.join(abs_values)} & {' & '.join(fluo_values)} \\\\")

            print("    \\midrule")

        print("    \\bottomrule")
        print("  \\end{tabular}")
        print(f"  \\caption{{Circular Dichroism Analysis (Part {table_num})}}")
        print(f"  \\label{{tab:cd_comparison{table_num}}}")
        print("\\end{table}\n\n")

def generate_latex_metrics_table(exp_data: dict, dic: dict, warnings: list) -> None:
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
                if exp_data[molecule]['display'] == False:
                    continue
                calc_data = dic[molecule][method][calc_type]
                if calc_data and 'energy' in calc_data:
                    if calc_data['energy'] is None:
                        warnings.append(f"Warning: 'energy' value is None for molecule {molecule}, method {method}, type {calc_type}. Skipping this value.")
                        continue
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

def generate_latex_metrics_table_molecules(exp_data: dict, dic: dict, warnings: list) -> None:
    """Print LaTeX code for the metrics summary table."""
    print("\\begin{table}[htbp]")
    print("  \\centering")
    print("  \\begin{tabular}{llrrr}")
    print("    \\toprule")
    print("    Method & Type & MSE & MAE & SD \\\\")
    print("    \\midrule")
    
    for data in MOLECULES_DATA:
        molecule = data["name"]
        display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
        for calc_type in ['ABS', 'FLUO']:
            calculated = []
            experimental = []
            for method in METHODS:
                calc_data = dic[molecule][method][calc_type]
                if calc_data and 'energy' in calc_data:
                    if calc_data['energy'] is None:
                        warnings.append(f"Warning: 'energy' value is None for molecule {molecule}, method {method}, type {calc_type}. Skipping this value.")
                        continue
                    calculated.append(calc_data['energy'])
                    experimental.append(exp_data[molecule][calc_type]['energy'])
            if len(calculated) == 0:
                mse_str = mae_str = sd_str = 'N/A'
            else:
                errors = [c - e for c, e in zip(calculated, experimental)]
                mse = np.mean(errors) if errors else np.nan
                mae = np.mean(np.abs(errors)) if errors else np.nan
                sd = np.std(errors) if len(errors) > 1 else np.nan
                mse_str = f"{mse:.2f}" if not np.isnan(mse) else 'N/A'
                mae_str = f"{mae:.2f}" if not np.isnan(mae) else 'N/A'
                sd_str = f"{sd:.2f}" if not np.isnan(sd) else 'N/A'
            print(f"    {display_name} & {calc_type} & {mse_str} & {mae_str} & {sd_str}\\\\")
    print("    \\bottomrule")
    print("  \\end{tabular}")
    print("  \\caption{\\centering Metrics Summary Comparing Computational Methods to Experimental Data for Molecules.}")
    print("  \\label{tab:metrics_molecules}")
    print("\\end{table}")
    
def generate_comparison_plots():
    """
    Generate comparison plots for absorption and fluorescence data:
    1. Individual plots for each method
    2. Global plots combining all methods
    """
    # Make sure the output directory exists
    os.makedirs("plot_comparison", exist_ok=True)
    
    # Assign unique markers to each molecule
    molecule_markers = {}
    available_markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x']
    
    # Create molecule to marker mapping
    for i, molecule in enumerate(sorted(exp_data.keys())):
        if exp_data[molecule]['display']:
            molecule_markers[molecule] = available_markers[i % len(available_markers)]
    
    # Data collectors for global plots
    all_abs_data = {method: [] for method in METHODS}
    all_fluo_data = {method: [] for method in METHODS}
    
    # 1. INDIVIDUAL METHOD PLOTS
    for method in METHODS:
        # ABSORPTION plot for current method
        abs_x, abs_y = [], []
        plt.figure(figsize=(10, 8))
        
        for molecule in sorted(exp_data.keys()):
            if not exp_data[molecule]['display']:
                continue
                
            display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
            comp_abs = dic[molecule][method]['ABS'].get('energy')
            exp_abs = exp_data[molecule]['ABS'].get('energy')
            
            if comp_abs and exp_abs and not np.isnan([comp_abs, exp_abs]).any():
                abs_x.append(exp_abs)
                abs_y.append(comp_abs)
                
                # Use consistent marker per molecule
                marker = molecule_markers[molecule]
                plt.scatter(exp_abs, comp_abs, 
                          marker=marker, 
                          color='blue',  # Use blue for all absorption
                          s=80,  # Larger points
                          alpha=0.8,
                          label=display_name)
                
                # Store for global plot
                all_abs_data[method].append((exp_abs, comp_abs, display_name, marker))
        
        # Complete and save the absorption plot if we have data
        if abs_x and abs_y:
            # Add diagonal reference line
            min_val = min(min(abs_x), min(abs_y))
            max_val = max(max(abs_x), max(abs_y))
            padding = 0.1 * (max_val - min_val)
            axis_min = min_val - padding
            axis_max = max_val + padding
            
            plt.plot([axis_min, axis_max], [axis_min, axis_max],
                    color='gray', linestyle='--', alpha=0.5)
            
            # Create legend with unique labels (no duplicates)
            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            plt.legend(by_label.values(), by_label.keys(), 
                      loc='lower right', title='Molecules')
            
            plt.xlim(axis_min, axis_max)
            plt.ylim(axis_min, axis_max)
            plt.title(f"Absorption ({method}): Experimental vs Computed Energies")
            plt.xlabel("Experimental Energy (eV)")
            plt.ylabel("Computed Energy (eV)")
            plt.grid(alpha=0.2)
            plt.tight_layout()
            plt.savefig(f"plot_comparison/absorption_{method}.pdf")
        plt.close()
        
        # FLUORESCENCE plot for current method
        fluo_x, fluo_y = [], []
        plt.figure(figsize=(10, 8))
        
        for molecule in sorted(exp_data.keys()):
            if not exp_data[molecule]['display']:
                continue
                
            display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
            comp_fluo = dic[molecule][method]['FLUO'].get('energy')
            exp_fluo = exp_data[molecule]['FLUO'].get('energy')
            
            if comp_fluo and exp_fluo and not np.isnan([comp_fluo, exp_fluo]).any():
                fluo_x.append(exp_fluo)
                fluo_y.append(comp_fluo)
                
                # Use consistent marker per molecule
                marker = molecule_markers[molecule]
                plt.scatter(exp_fluo, comp_fluo, 
                          marker=marker, 
                          color='red',  # Use red for all fluorescence
                          s=80,  # Larger points
                          alpha=0.8,
                          label=display_name)
                
                # Store for global plot
                all_fluo_data[method].append((exp_fluo, comp_fluo, display_name, marker))
        
        # Complete and save the fluorescence plot if we have data
        if fluo_x and fluo_y:
            # Add diagonal reference line
            min_val = min(min(fluo_x), min(fluo_y))
            max_val = max(max(fluo_x), max(fluo_y))
            padding = 0.1 * (max_val - min_val)
            axis_min = min_val - padding
            axis_max = max_val + padding
            
            plt.plot([axis_min, axis_max], [axis_min, axis_max],
                    color='gray', linestyle='--', alpha=0.5)
            
            # Create legend with unique labels (no duplicates)
            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            plt.legend(by_label.values(), by_label.keys(), 
                      loc='lower right', title='Molecules')
            
            plt.xlim(axis_min, axis_max)
            plt.ylim(axis_min, axis_max)
            plt.title(f"Fluorescence ({method}): Experimental vs Computed Energies")
            plt.xlabel("Experimental Energy (eV)")
            plt.ylabel("Computed Energy (eV)")
            plt.grid(alpha=0.2)
            plt.tight_layout()
            plt.savefig(f"plot_comparison/fluorescence_{method}.pdf")
        plt.close()
    
    # 2. GLOBAL PLOTS
    # 2.1 GLOBAL ABSORPTION PLOT
    plt.figure(figsize=(12, 9))
    all_abs_x, all_abs_y = [], []
    
    # Plot data for each method with consistent coloring
    for method_idx, method in enumerate(METHODS):
        if all_abs_data[method]:  # Only if there's data for this method
            color = plt.cm.tab10.colors[method_idx % len(plt.cm.tab10.colors)]
            
            for exp_val, comp_val, molecule_name, marker in all_abs_data[method]:
                all_abs_x.append(exp_val)
                all_abs_y.append(comp_val)
                plt.scatter(exp_val, comp_val,
                           marker=marker,
                           color=color,
                           s=80,
                           alpha=0.8)
    
    # Complete the absorption global plot if we have data
    if all_abs_x and all_abs_y:
        # Add diagonal reference line
        min_val = min(min(all_abs_x), min(all_abs_y))
        max_val = max(max(all_abs_x), max(all_abs_y))
        padding = 0.1 * (max_val - min_val)
        axis_min = min_val - padding
        axis_max = max_val + padding
        
        plt.plot([axis_min, axis_max], [axis_min, axis_max],
                color='gray', linestyle='--', alpha=0.5)
        
        # Create legends (molecules and methods)
        from matplotlib.lines import Line2D
        
        # Method color legend
        method_handles = []
        for i, method in enumerate(METHODS):
            if any(all_abs_data[method]):
                color = plt.cm.tab10.colors[i % len(plt.cm.tab10.colors)]
                method_handles.append(Line2D([0], [0], color=color, lw=4, label=method))
        
        # Molecule marker legend  
        molecule_handles = []
        for molecule, marker in molecule_markers.items():
            if exp_data[molecule]['display']:
                display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
                molecule_handles.append(Line2D([0], [0], marker=marker, color='black', 
                                             markersize=8, linestyle='None', label=display_name))
        
        # Add the legends
        first_legend = plt.legend(handles=molecule_handles, loc='lower right', 
                                 title='Molecules', fontsize=9)
        plt.gca().add_artist(first_legend)
        
        plt.legend(handles=method_handles, loc='upper left', 
                  title='Methods', fontsize=9)
        
        plt.xlim(axis_min, axis_max)
        plt.ylim(axis_min, axis_max)
        plt.title("Absorption: Experimental vs Computed Energies (All Methods)")
        plt.xlabel("Experimental Energy (eV)")
        plt.ylabel("Computed Energy (eV)")
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig("plot_comparison/absorption_comparison.pdf")
    plt.close()
    
    # 2.2 GLOBAL FLUORESCENCE PLOT
    plt.figure(figsize=(12, 9))
    all_fluo_x, all_fluo_y = [], []
    
    # Plot data for each method with consistent coloring
    for method_idx, method in enumerate(METHODS):
        if all_fluo_data[method]:  # Only if there's data for this method
            color = plt.cm.tab10.colors[method_idx % len(plt.cm.tab10.colors)]
            
            for exp_val, comp_val, molecule_name, marker in all_fluo_data[method]:
                all_fluo_x.append(exp_val)
                all_fluo_y.append(comp_val)
                plt.scatter(exp_val, comp_val,
                           marker=marker,
                           color=color,
                           s=80,
                           alpha=0.8)
    
    # Complete the fluorescence global plot if we have data
    if all_fluo_x and all_fluo_y:
        # Add diagonal reference line
        min_val = min(min(all_fluo_x), min(all_fluo_y))
        max_val = max(max(all_fluo_x), max(all_fluo_y))
        padding = 0.1 * (max_val - min_val)
        axis_min = min_val - padding
        axis_max = max_val + padding
        
        plt.plot([axis_min, axis_max], [axis_min, axis_max],
                color='gray', linestyle='--', alpha=0.5)
        
        # Create legends (molecules and methods)
        from matplotlib.lines import Line2D
        
        # Method color legend
        method_handles = []
        for i, method in enumerate(METHODS):
            if any(all_fluo_data[method]):
                color = plt.cm.tab10.colors[i % len(plt.cm.tab10.colors)]
                method_handles.append(Line2D([0], [0], color=color, lw=4, label=method))
        
        # Molecule marker legend  
        molecule_handles = []
        for molecule, marker in molecule_markers.items():
            if exp_data[molecule]['display']:
                display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
                molecule_handles.append(Line2D([0], [0], marker=marker, color='black', 
                                             markersize=8, linestyle='None', label=display_name))
        
        # Add the legends
        first_legend = plt.legend(handles=molecule_handles, loc='lower right', 
                                 title='Molecules', fontsize=9)
        plt.gca().add_artist(first_legend)
        
        plt.legend(handles=method_handles, loc='upper left', 
                  title='Methods', fontsize=9)
        
        plt.xlim(axis_min, axis_max)
        plt.ylim(axis_min, axis_max)
        plt.title("Fluorescence: Experimental vs Computed Energies (All Methods)")
        plt.xlabel("Experimental Energy (eV)")
        plt.ylabel("Computed Energy (eV)")
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig("plot_comparison/fluorescence_comparison.pdf")
    plt.close()

def generate_comparison_plots_swp():
    """Generate comparison plots with regression analysis"""
    for method in METHODS:
        plt.figure(figsize=(8, 6))
        abs_x, abs_y, abs_labels = [], [], []
        fluo_x, fluo_y, fluo_labels = [], [], []
        
        for molecule in exp_data:
            display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
            if exp_data[molecule]['display'] == False:
                continue

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
                for i, label in enumerate(abs_labels):
                    plt.text(abs_x[i], abs_y[i], label,
                             fontsize=8, color='blue',
                             ha='right', va='bottom', alpha=0.7
                             )
            if fluo_x:
                plt.scatter(fluo_x, fluo_y, c='red', label='Fluorescence')
                for i, label in enumerate(fluo_labels):
                    plt.text(fluo_x[i], fluo_y[i], label,
                             fontsize=8, color='red',
                             ha='left', va='top', alpha=0.7
                             )

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

def test_CD_properties():
    """Generate test LaTeX tables comparing both g-factor calculation methods"""
    max_molecule_per_table = 2  # Smaller chunks since we have more columns
    chunks = [MOLECULES_DATA[i:i+max_molecule_per_table] for i in range(0, len(MOLECULES_DATA), max_molecule_per_table)]

    for table_num, chunk in enumerate(chunks, 1):
        print(f"\\begin{{table}}[htbp]")
        print("  \\centering")
        print("  \\tiny")  # Using tiny font due to many columns
        print("  \\begin{tabular}{llccccccc}")
        print("    \\toprule")
        print("    \\multirow{2}{*}{Molecule} & \\multirow{2}{*}{Method} & \\multicolumn{4}{c}{Absorption (Length Gauge)} & \\multicolumn{3}{c}{Emission (Length Gauge)} \\\\")
        print("    \\cmidrule(lr){3-6} \\cmidrule(lr){7-9}")
        print("    & & $g_{abs}$ (4R/D) & $g_{abs}$ (4|m|cos$\\theta$/|$\\mu$|) & $|\\vec{D}|$ & $|\\vec{M}|$ & $g_{lum}$ (4R/D) & $g_{lum}$ (4|m|cos$\\theta$/|$\\mu$|) & $\\theta_{MD}$ \\\\")
        print("    \\midrule")

        for data in chunk:
            molecule = data["name"]
            if molecule not in exp_data:
                continue
                
            display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
            exp_gabs = exp_data[molecule]['ABS'].get('gabs', np.nan)
            exp_glum = data.get("exp_glum", np.nan)

            # Experimental row
            exp_row = [
                "Exp",
                f"{exp_gabs:.1f}" if not np.isnan(exp_gabs) else "N/A",
                "N/A",  # No alternative calculation for experimental
                "N/A",  # No vector norms for experimental
                "N/A",
                f"{exp_glum:.1f}" if not np.isnan(exp_glum) else "N/A",
                "N/A",  # No alternative calculation for experimental
                "N/A"   # No angle data for experimental
            ]
            print(f"    \\multirow{{{len(METHODS)+1}}}{{*}}{{{display_name}}} & " + " & ".join(exp_row) + " \\\\\\\\")

            # Computational rows with both calculation methods
            for method in METHODS:
                abs_data = dic[molecule][method]['ABS']
                fluo_data = dic[molecule][method]['FLUO']

                # Format absorption data with both calculation methods
                gabs_length = abs_data.get('gabs_length', np.nan)
                gabs_length_alt = abs_data.get('gabs_length_alt', np.nan)
                d_norm = abs_data.get('D_norm', np.nan)
                m_norm = abs_data.get('M_norm', np.nan)
                
                abs_values = [
                    f"{gabs_length:.1f}" if not np.isnan(gabs_length) else "N/A",
                    f"{gabs_length_alt:.1f}" if not np.isnan(gabs_length_alt) else "N/A",
                    f"{d_norm:.3f}" if not np.isnan(d_norm) else "N/A",
                    f"{m_norm:.3f}" if not np.isnan(m_norm) else "N/A"
                ]

                # Format fluorescence data with both calculation methods
                glum_length = fluo_data.get('glum_length', np.nan)
                glum_length_alt = fluo_data.get('glum_length_alt', np.nan)
                angle_md_fluo = fluo_data.get('angle_MD', np.nan)
                
                fluo_values = [
                    f"{glum_length:.1f}" if not np.isnan(glum_length) else "N/A",
                    f"{glum_length_alt:.1f}" if not np.isnan(glum_length_alt) else "N/A",
                    f"{angle_md_fluo:.1f}" if not np.isnan(angle_md_fluo) else "N/A"
                ]

                print(f"     & {method} & {' & '.join(abs_values)} & {' & '.join(fluo_values)} \\\\")

            print("    \\midrule")

        print("    \\bottomrule")
        print("  \\end{tabular}")
        print(f"  \\caption{{Comparison of CD Calculation Methods - Length Gauge (Part {table_num})}}")
        print(f"  \\label{{tab:cd_comparison_methods{table_num}}}")
        print("\\end{table}\n\n")

    # Second table for velocity gauge properties with both calculation methods
    for table_num, chunk in enumerate(chunks, 1):
        print(f"\\begin{{table}}[htbp]")
        print("  \\centering")
        print("  \\tiny")
        print("  \\begin{tabular}{llccccccc}")
        print("    \\toprule")
        print("    \\multirow{2}{*}{Molecule} & \\multirow{2}{*}{Method} & \\multicolumn{4}{c}{Absorption (Velocity Gauge)} & \\multicolumn{3}{c}{Emission (Velocity Gauge)} \\\\")
        print("    \\cmidrule(lr){3-6} \\cmidrule(lr){7-9}")
        print("    & & $g_{abs}^{vel}$ (4R/D) & $g_{abs}^{vel}$ (4|m|cos$\\theta$/|$\\mu$|) & $|\\vec{P}|$ & $|\\vec{M}|$ & $g_{lum}^{vel}$ (4R/D) & $g_{lum}^{vel}$ (4|m|cos$\\theta$/|$\\mu$|) & $\\theta_{MP}$ \\\\")
        print("    \\midrule")

        for data in chunk:
            molecule = data["name"]
            if molecule not in exp_data:
                continue
                
            display_name = MOLECULE_NAME_MAPPING.get(molecule, molecule)
            exp_gabs = exp_data[molecule]['ABS'].get('gabs', np.nan)
            exp_glum = data.get("exp_glum", np.nan)

            # Experimental row - no velocity gauge data for experimental
            exp_row = [
                "Exp",
                f"{exp_gabs:.1f}" if not np.isnan(exp_gabs) else "N/A",
                "N/A",  # No alternative calculation for experimental
                "N/A",  # No vector norms for experimental
                "N/A",
                f"{exp_glum:.1f}" if not np.isnan(exp_glum) else "N/A",
                "N/A",  # No alternative calculation for experimental
                "N/A"   # No angle data for experimental
            ]
            print(f"    \\multirow{{{len(METHODS)+1}}}{{*}}{{{display_name}}} & " + " & ".join(exp_row) + " \\\\\\\\")

            # Computational rows with both calculation methods
            for method in METHODS:
                abs_data = dic[molecule][method]['ABS']
                fluo_data = dic[molecule][method]['FLUO']

                # Format velocity gauge absorption data with both calculation methods
                gabs_velocity = abs_data.get('gabs_velocity', np.nan)
                gabs_velocity_alt = abs_data.get('gabs_velocity_alt', np.nan)
                p_norm = abs_data.get('P_norm', np.nan)
                m_norm = abs_data.get('M_norm', np.nan)
                
                abs_vel_values = [
                    f"{gabs_velocity:.1f}" if not np.isnan(gabs_velocity) else "N/A",
                    f"{gabs_velocity_alt:.1f}" if not np.isnan(gabs_velocity_alt) else "N/A",
                    f"{p_norm:.3f}" if not np.isnan(p_norm) else "N/A",
                    f"{m_norm:.3f}" if not np.isnan(m_norm) else "N/A"
                ]

                # Format velocity gauge fluorescence data with both calculation methods
                glum_velocity = fluo_data.get('glum_velocity', np.nan)
                glum_velocity_alt = fluo_data.get('glum_velocity_alt', np.nan)
                angle_mp_fluo = fluo_data.get('angle_MP', np.nan)
                
                fluo_vel_values = [
                    f"{glum_velocity:.1f}" if not np.isnan(glum_velocity) else "N/A",
                    f"{glum_velocity_alt:.1f}" if not np.isnan(glum_velocity_alt) else "N/A",
                    f"{angle_mp_fluo:.1f}" if not np.isnan(angle_mp_fluo) else "N/A"
                ]

                print(f"     & {method} & {' & '.join(abs_vel_values)} & {' & '.join(fluo_vel_values)} \\\\")

            print("    \\midrule")

        print("    \\bottomrule")
        print("  \\end{tabular}")
        print(f"  \\caption{{Comparison of CD Calculation Methods - Velocity Gauge (Part {table_num})}}")
        print(f"  \\label{{tab:cd_comparison_methods_vel{table_num}}}")
        print("\\end{table}\n\n")
def main():
    """Main function to coordinate data collection and LaTeX table generation."""
    warnings = [] # Store the warning messages
    # Collect computational data
    for data in MOLECULES_DATA:
        molecule = data["name"]
        abs_solvant_correction = get_solvatation_correction(molecule, "MO62Xtddft", 'ABS', warnings)
        fluo_solvant_correction = get_solvatation_correction(molecule, "MO62Xtddft", 'FLUO', warnings)
        for method in METHODS:
            if method != "CC2":
                abs_result = parse_file_orca(molecule, method, 'ABS', abs_solvant_correction)
                fluo_result = parse_file_orca(molecule, method, 'FLUO', fluo_solvant_correction)

            else:
                abs_result = parse_file_turbomole(molecule, method, 'ABS', abs_solvant_correction)
                fluo_result = parse_file_turbomole(molecule, method, 'FLUO', fluo_solvant_correction)

            if abs_result:
                dic[molecule][method]['ABS'] = abs_result
            if fluo_result:
                dic[molecule][method]['FLUO'] = fluo_result
    
    # Print LaTeX tables
    generate_latex_tables()
    print("\n\n")  # Separate the tables with some newlines
    generate_latex_metrics_table(exp_data, dic, warnings)
    print("\n\n")  # Separate the tables with some newlines
    generate_latex_metrics_table_molecules(exp_data, dic, warnings)
    print("\n\n")  # Separate the tables with some newlines
    generate_CD()
    generate_latex_tables_CD()
    for warning in warnings:
        print(warning)    
    generate_comparison_plots()
    test_CD_properties()
    print("")
    print(f"Plots done")

if __name__ == "__main__":
    main()

