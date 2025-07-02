#!/usr/bin/env python3
"""
Quantum Chemistry Output Parser for Electronic Transition and Chiroptic Analysis

This module provides functions to parse ORCA and TURBOMOLE ricc2 output files
to extract electronic transition data for circular dichroism (CD) analysis.
It handles extraction and calculation of:
- Transition energies (eV)
- Oscillator strengths (length and velocity gauges)
- Rotational strengths (length and velocity gauges)
- Transition electric and magnetic dipole moments (length and velocity gauges)
- Dissymmetry factors (g-factors)
- Angles between transition electric and magnetic dipole moments (length and velocity gauges)

The module supports both ORCA and TURBOMOLE ricc2 output formats with appropriate
parsing strategies for each.

Usage:
    # Get electronic transition and chiroptic data
    data = parse_file(molecule, method, calc_type, solvant_correction)

    # Get solvatation correction
    correction = get_solvatation_correction(molecule, method, calc_type, warnings_list)
"""

from math import sqrt
import re
import os
import warnings
import numpy as np
from constants import nm_to_eV, au_to_cgs_charge_length, eV_to_au, fine_structure_constant, h_cgs, pi, elementary_charge_cgs, m_e_cgs, eV_to_cgs

def parse_file(molecule: str, method_optimization: str, method_luminescence: str, solvant_correction: float=0, working_dir=None) -> dict:
    """
    Parse ORCA or TURBOMOLE ricc2 output files for electronic transition data values.

    This function selects the appropriate parser based on the calculation method and
    processes the output file to extract transition energies, oscillator strengths,
    rotational strengths, and transition dipole moments. It also calculates chiroptic
    properties such as dissymmetry factors and angles between dipole moments.
    
    Parameters
    ----------
    molecule : str
        Name of the molecule (used in file path construction)
    method_optimization : str
        Optimization method (e.g., "OPTGS", "OPTES@MO62X", "OPTES@MO62Xtddft"). Determines the parser and file path.
    method_luminescence : str
        Optimization method (e.g., "ABS@CC2", "FLUO@MO62Xtddft"). Determines the parser and file path.
    solvant_correction : float, optional
        Energy correction for solvent effects for post-HF method in eV. Default is 0.
    working_dir : str, optional
        Directory from which the calculations are submited. Defaults to current working directory.
        
    Returns
    -------
    dict
        Dictionary containing extracted and calculated values including:
        - energy
        - oscillator strengths (length and velocity gauges)
        - rotational strengths (length and velocity gauges)
        - transition dipole moments (electric, magnetic)
        - vector norms squared (D2, P2, M2)
        - dissymmetry factors
        - angles between dipole moments
    """
    if working_dir is None:
        working_dir = os.getcwd()
    
    # Select appropriate file path and parser based on method
    if "CC2" in method_luminescence or "ADC2_COSMO" in method_luminescence or "CC2_COSMO" in method_luminescence:
        filename = f"{working_dir}/{molecule}/{molecule}{method_optimization}-{method_luminescence}/ricc2.out"
        parser_func = parse_turbomole_format
    else:
        filename = f"{working_dir}/{molecule}/{molecule}{method_optimization}-{method_luminescence}/{molecule}{method_optimization}-{method_luminescence}.out"
        parser_func = parse_orca_format
    
    if not os.path.exists(filename):
        #warnings.warn(f"⚠️ Missing file: {filename}", UserWarning)
        return initialize_data()
    
    try:
        data = parser_func(filename, solvant_correction)
    except Exception as e:
        warnings.warn(f"⚠️ Error reading file {filename}: {str(e)}", UserWarning)
        return initialize_data()
    
    generate_CD(data)
    return data
    
def initialize_data():
    """
    Initialize a dictionary with default values for electronic transition data.
    
    Returns
    -------
    dict
        Dictionary with keys for energy, wavelength, oscillator strengths, 
        rotational strengths, dipole moments, and other properties initialized to NaN.
    """
    return {
        'energy': float('nan'), # in eV
        'wavelength': float('nan'), # in nm
        'oscillator_strength_length': float('nan'), # dimensionless
        'oscillator_strength_velocity': float('nan'), # dimensionless
        'rotational_strength_length': float('nan'), # 1e40*cgs (cgs units)
        'rotational_strength_velocity': float('nan'), # 1e40*cgs (cgs units)
        'dipole_strength_length': float('nan'), # 1e40*cgs (cgs units)
        'dipole_strength_velocity': float('nan'), # 1e40*cgs (cgs units)
        'DX': float('nan'), 'DY': float('nan'), 'DZ': float('nan'), # (e*a_0 = eħ / (me * c * α))**2 (atomic units)
        'PX': float('nan'), 'PY': float('nan'), 'PZ': float('nan'), 
        'MX': float('nan'), 'MY': float('nan'), 'MZ': float('nan'), # (mu_B = eħ/ (2me) )**2 (atomic units)
        'D2': float('nan'), 'P2': float('nan'), 'M2': float('nan'), 
        'dissymmetry_factor_strength_length': float('nan'), # 10**-4
        'dissymmetry_factor_strength_velocity': float('nan'), # 10**-4
        'dissymmetry_factor_vector_length': float('nan'),  # 10**-4
        'dissymmetry_factor_vector_velocity': float('nan'), # 10**-4
        'angle_length': float('nan'), # in degrees
        'angle_velocity': float('nan') # in degrees
    }
     
def parse_orca_format(filename: str, solvant_correction: float=0):
    """
    Parse ORCA output files for electronic transition data values.
    
    Returns a dictionary with formatted values, including energy (eV), wavelength (nm), 
    oscillator and rotational strengths in both length and velocity gauges, 
    as well as transition electric and magnetic dipole moments.
    """
    data = initialize_data()
    with open(filename, 'r') as f:
        # The following functionnals create a imaginary transition thus the second need to be taken
#        if any(x in filename for x in ["ABS@MO62X", "ABS@CAM-B3LYP", "ABS@B3LYP", "ABS@B2PLYP", "ABS@CC2"]) and "Boranil_NO2+RBINOL_H" in filename:
#            pattern = (
#            r'0-1\S+\s+->\s+2-1\S+\s+'
#            r'\s+(?P<energy_eV>[-+]?\d+\.\d+)'
#            r'\s+(?P<energy_rcm>[-+]?\d+\.\d+)'
#            r'\s+(?P<wavelength>[-+]?\d+\.\d+)'
#            r'\s+(?P<strength>[-+]?\d+\.\d+)'
#            r'\s+(?P<transition_dipole1>[-+]?\d+\.\d+)'
#            r'\s+(?P<transition_dipole2>[-+]?\d+\.\d+)'
#            r'\s+(?P<transition_dipole3>[-+]?\d+\.\d+)'
#            r'\s+(?P<transition_dipole4>[-+]?\d+\.\d+)?'
#            )
#        else:
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
                        data['energy'] = float(match.group('energy_eV')) + solvant_correction
                        data['wavelength'] = nm_to_eV / data['energy']
                        data['oscillator_strength_length'] = float(match.group('strength'))
                        data['D2'] = float(match.group('transition_dipole1'))
                        data['DX'] = float(match.group('transition_dipole2'))
                        data['DY'] = float(match.group('transition_dipole3'))
                        data['DZ'] = float(match.group('transition_dipole4'))
                        data['dipole_strength_length'] = data['D2'] * au_to_cgs_charge_length**2
                    elif counter == 1:
                        data['oscillator_strength_velocity'] = float(match.group('strength'))
                        energy_au = data['energy'] / eV_to_au
                        data['P2'] = float(match.group('transition_dipole1')) / energy_au**2 # Velocity gauge convert to length value
                        data['PX'] = - float(match.group('transition_dipole2')) / energy_au
                        data['PY'] = - float(match.group('transition_dipole3')) / energy_au
                        data['PZ'] = - float(match.group('transition_dipole4')) / energy_au
                        data['dipole_strength_velocity'] = data['P2'] * au_to_cgs_charge_length**2
                    elif counter == 2:
                        data['rotational_strength_length'] = float(match.group('strength'))
                        data['MX'] = float(match.group('transition_dipole1'))
                        data['MY'] = float(match.group('transition_dipole2'))
                        data['MZ'] = float(match.group('transition_dipole3'))
                        data['M2'] = data['MX']**2 + data['MY']**2 + data['MZ']**2
                    elif counter == 3:
                        data['rotational_strength_velocity'] = float(match.group('strength'))
                        return data
                    counter += 1
                except (ValueError, IndexError) as e:
                    warnings.warn(f"⚠️ Parsing error in {filename}: {str(e)}", UserWarning)
                    return data
    warnings.warn(f"⚠️ Missing data in {filename}", UserWarning)
    return data

def parse_turbomole_format(filename: str, solvant_correction: float=0):
    """
    Parse TURBOMOLE output files for electronic transition data values.

    Returns a dictionary with formatted values, including energy (eV), wavelength (nm), 
    oscillator and rotational strengths in both length and velocity gauges, 
    as well as transition electric and magnetic dipole moments.
    """
    data = initialize_data()
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
        'oscillator_strength_length': r'oscillator strength \(length gauge\)\s+:\s+(\S+)',
        'oscillator_strength_velocity': r'oscillator strength \(velocity gauge\)\s+:\s+(\S+)',
        'rotational_strength_length': r'Rotator strength \(length gauge\)\s+:\s+(\S+)\s+10\^\(-40\)\*erg\*cm\^3',
        'rotational_strength_velocity': r'Rotator strength \(velocity gauge\)\s+:\s+(\S+)\s+10\^\(-40\)\*erg\*cm\^3',
    }

    search_order = [
        'energy', 
        'DX', 'DY', 'DZ',
        'PX', 'PY', 'PZ',
        'MX', 'MY', 'MZ',
        'oscillator_strength_length',
        'oscillator_strength_velocity',
        'rotational_strength_length',
        'rotational_strength_velocity'
    ]
    
    found_fields = set()
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        line_idx = 0
        # Process each field in the expected order; then one if found move to the next and search in the next line
        for field in search_order:
            if field not in patterns:
                warnings.warn(f"⚠️ Field '{field}' not defined in patterns dictionary", UserWarning)
                continue
                
            pattern = patterns[field]
            field_found = False
            while line_idx < len(lines) and not field_found:
                line = lines[line_idx]
                match = re.search(pattern, line)
                if match:
                    try:
                        if field == 'energy':
                            data[field] = float(match.group(1)) + solvant_correction
                            data['wavelength'] = nm_to_eV / data['energy']
                            energy_au = data['energy'] / eV_to_au
                        elif field == 'PX' or field == 'PY' or field == 'PZ':
                            data[field] = - float(match.group(1)) / energy_au # type: ignore # Velocity gauge convert to length value
                        else:
                            data[field] = float(match.group(1))                        
                        found_fields.add(field)
                        field_found = True
                        
                    except (ValueError, IndexError) as e:
                        warnings.warn(f"⚠️ Error parsing {field} in {filename}: {str(e)}", UserWarning)
                line_idx += 1
    
    # Check if any fields are missing
    missing_fields = set(search_order) - found_fields
    if missing_fields:
        warnings.warn(f"⚠️ Missing data in {filename}: {', '.join(missing_fields)}", UserWarning)
    if not any(field in missing_fields for field in ['DX', 'DY', 'DZ']):
        data['D2'] = data['DX']**2 + data['DY']**2 + data['DZ']**2
        #data['dipole_strength_length'] = data['D2'] * au_to_cgs_charge_length**2
    if not any(field in missing_fields for field in ['PX', 'PY', 'PZ']):
        data['P2'] = data['PX']**2 + data['PY']**2 + data['PZ']**2
        #data['dipole_strength_velocity'] = data['P2'] * au_to_cgs_charge_length**2
    if not any(field in missing_fields for field in ['MX', 'MY', 'MZ']):
        data['M2'] = data['MX']**2 + data['MY']**2 + data['MZ']**2
    if not any(field in missing_fields for field in ['oscillator_strength_length', 'oscillator_strength_velocity']):
        data['dipole_strength_length'] = 3 * h_cgs**2 * elementary_charge_cgs**2 / (8 * pi**2 * m_e_cgs * eV_to_cgs * data['energy']) * data['oscillator_strength_length'] * 1e40
        data['dipole_strength_velocity'] = (3 * h_cgs**2 * elementary_charge_cgs**2) / (8 * pi**2 * m_e_cgs * eV_to_cgs * data['energy']) * data['oscillator_strength_velocity'] * 1e40
    return data

def get_solvatation_correction(molecule: str, method_optimization: str, method_luminescence: str, warnings_list: list, working_dir=None) -> float:
    """
    Calculate solvation energy correction from the difference between solvated and non-solvated calculations.
    
    Args:
        molecule: Molecule name
        method: Calculation method
        calc_type: Type of calculation
        warnings_list: List to append warnings to
        working_dir: Directory containing calculations (defaults to current directory)
        
    Returns:
        Solvation energy correction in eV
    """
    solv = parse_file(molecule, method_optimization, method_luminescence, working_dir=working_dir)
    no_solv = parse_file(molecule, method_optimization, f"{method_luminescence}_nosolv", working_dir=working_dir)
    if solv['energy'] and no_solv['energy']:
        return solv['energy'] - no_solv['energy']
    else:
        warnings_list.append(f"⚠️ No solvatation correction for {molecule} in {method_optimization} with {method_luminescence}")
        return 0
    
def generate_CD(data: dict):
    """
    Calculate chiroptic parameters for both length and velocity gauge with the data given:
    - dissymmetry factor
    - Vector norms for magnetic and electric dipole moments
    - Angles between magnetic and electric dipole moments
    The data are stored in the data dictionary.
    """
    
    # Calculate dissymmetry factor
    if data.get('oscillator_strength_length') and data.get('oscillator_strength_length', 0) != 0:
        data['dissymmetry_factor_strength_length'] = 4 * data.get('rotational_strength_length', 0) / data.get('dipole_strength_length')  * 1e4
           
    if data.get('oscillator_strength_velocity') and data.get('oscillator_strength_velocity', 0) != 0:
        data['dissymmetry_factor_strength_velocity'] = 4 * data.get('rotational_strength_velocity', 0) / data.get('dipole_strength_velocity')  * 1e4
    
    # Calculate angles (in degrees) between magnetic and electric dipole moments
    for gauge, e_prefix, in [('length', 'D'), ('velocity', 'P')]:
        e_coordinates = [f'{e_prefix}X', f'{e_prefix}Y', f'{e_prefix}Z']
        m_coordinates = ['MX', 'MY', 'MZ']
        required_keys = m_coordinates + e_coordinates + ['M2', f'{e_prefix}2']

        # Check if all necessary components and norms are available and are valid numbers
        if all(not np.isnan(data.get(key, float('nan'))) for key in required_keys):
            m2_val = data['M2']
            e2_val = data[f'{e_prefix}2']

            # Ensure norms are positive to avoid issues with sqrt and division by zero
            if m2_val > 1e-9 and e2_val > 1e-9:
                dot_product = sum(data[m] * data[e] for m, e in zip(m_coordinates, e_coordinates))
                cos_angle = np.clip(dot_product / sqrt(m2_val * e2_val), -1.0, 1.0) # Clip for numerical stability

                data[f'angle_{gauge}'] = np.degrees(np.arccos(cos_angle))
                # Dissymmetry factor calculation based on vector components
                data[f'dissymmetry_factor_vector_{gauge}'] = 4 * sqrt(m2_val) * cos_angle / sqrt(e2_val) * 1e4 * (-fine_structure_constant) # Miss a /2 and I don't know why there is a minus sign
    return
