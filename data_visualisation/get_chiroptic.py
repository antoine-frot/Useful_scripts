#!/usr/bin/env python3
import os
import argparse
import numpy as np
from electronic_transition_parser import parse_orca_format, parse_turbomole_format, generate_CD

def parse_custom_file(filename: str):
    """
    Parse a quantum chemistry output file using either ORCA or TURBOMOLE parser based on user choice.
    
    Parameters
    ----------
    filename : str
        Path to the file to be parsed
    
    Returns
    -------
    None
        Results are saved to chiroptic.txt
    """
    # Initialize data dictionary with NaN values
    data = {
        'energy': float('nan'), # in eV
        'wavelength': float('nan'), # in nm
        'oscillator_strength_length': float('nan'),
        'oscillator_strength_velocity': float('nan'), # dimensionless
        'rotational_strength_length': float('nan'), # dimensionless (atomic units)
        'rotational_strength_velocity': float('nan'), # dimensionless (atomic units)
        'dipole_strength_length': float('nan'), # (e*a_0)**2 (atomic units)
        'dipole_strength_velocity': float('nan'), # (e*a_0)**2 (atomic units)
        'DX': float('nan'), 'DY': float('nan'), 'DZ': float('nan'), 
        'PX': float('nan'), 'PY': float('nan'), 'PZ': float('nan'),
        'MX': float('nan'), 'MY': float('nan'), 'MZ': float('nan'),
        'dissymmetry_factor_strength_length': float('nan'), # 10**-4
        'dissymmetry_factor_strength_velocity': float('nan'), # 10**-4
        'dissymmetry_factor_vector_length': float('nan'),  # 10**-4
        'dissymmetry_factor_vector_velocity': float('nan'), # 10**-4
        'angle_length': float('nan'), # in degrees
        'angle_velocity': float('nan'), # in degrees
    }
    
    # Check if file exists
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' does not exist.")
        return
    
    # Get user input for parser selection
    while True:
        parser_choice = input("Choose parser (1 for ORCA, 2 for TURBOMOLE): ").strip()
        if parser_choice in ('1', '2'):
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    try:
        # Parse file based on user choice
        if parser_choice == '1':
            print(f"Parsing {filename} with ORCA parser...")
            parse_orca_format(data, filename)
        else:
            print(f"Parsing {filename} with TURBOMOLE parser...")
            parse_turbomole_format(data, filename)
        
        # Calculate CD parameters
        generate_CD(data)
        
        # Write results to chiroptic.txt
        with open('chiroptic.txt', 'w') as f:
            f.write(f"Chiroptic Analysis Results for {os.path.basename(filename)}\n")
            f.write("=" * 60 + "\n\n")
            
            # Write data in organized sections
            f.write("Energy and Wavelength:\n")
            f.write(f"  Energy: {data['energy']:.4f} eV\n")
            if 'wavelength' in data and not np.isnan(data.get('wavelength', float('nan'))):
                f.write(f"  Wavelength: {data['wavelength']:.2f} nm\n")
            else:
                f.write(f"  Wavelength: {1239.84193 / data['energy']:.2f} nm (calculated)\n")
            f.write("\n")
            
            f.write("Oscillator Strengths:\n")
            f.write(f"  Length gauge: {data['oscillator_strength_length']:.6f}\n")
            f.write(f"  Velocity gauge: {data['oscillator_strength_velocity']:.6f}\n")
            f.write("\n")
            
            f.write("Rotational Strengths:\n")
            f.write(f"  Length gauge: {data['rotational_strength_length']:.6f}\n")
            f.write(f"  Velocity gauge: {data['rotational_strength_velocity']:.6f}\n")
            f.write("\n")
            
            f.write("Transition Electric Dipole Moment (Length):\n")
            f.write(f"  DX: {data['DX']:.6f}\n")
            f.write(f"  DY: {data['DY']:.6f}\n")
            f.write(f"  DZ: {data['DZ']:.6f}\n")
            f.write(f"  |D|²: {data['dipole_strength_length']:.6f}\n")
            f.write("\n")
            
            f.write("Transition Electric Dipole Moment (Velocity):\n")
            f.write(f"  PX: {data['PX']:.6f}\n")
            f.write(f"  PY: {data['PY']:.6f}\n")
            f.write(f"  PZ: {data['PZ']:.6f}\n")
            f.write(f"  |P|²: {data['dipole_strength_velocity']:.6f}\n")
            f.write("\n")
            
            f.write("Transition Magnetic Dipole Moment:\n")
            f.write(f"  MX: {data['MX']:.6f}\n")
            f.write(f"  MY: {data['MY']:.6f}\n")
            f.write(f"  MZ: {data['MZ']:.6f}\n")
            if 'M2' in data:
                f.write(f"  |M|²: {data['M2']:.6f}\n")
            f.write("\n")
            
            f.write("Dissymmetry Factors (g-factors, 10^-4):\n")
            f.write(f"  Length gauge (from strength): {data['dissymmetry_factor_strength_length']:.6f}\n")
            f.write(f"  Velocity gauge (from strength): {data['dissymmetry_factor_strength_velocity']:.6f}\n")
            f.write(f"  Length gauge (from vectors): {data['dissymmetry_factor_vector_length']:.6f}\n")
            f.write(f"  Velocity gauge (from vectors): {data['dissymmetry_factor_vector_velocity']:.6f}\n")
            f.write("\n")
            
            f.write("Angles between Electric and Magnetic Dipole Moments:\n")
            f.write(f"  Length gauge: {data.get('angle_length', float('nan')):.2f} degrees\n")
            f.write(f"  Velocity gauge: {data.get('angle_velocity', float('nan')):.2f} degrees\n")
        
        print(f"Results saved to chiroptic.txt")
        
    except Exception as e:
        print(f"Error parsing file: {str(e)}")
        
    return

def main():
    """Main function to handle command-line arguments and execute the parser."""
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description='Parse quantum chemistry output files for electronic transition data.',
        epilog='Example: %(prog)s path/to/output_file.out'
    )
    
    # Add arguments
    parser.add_argument(
        'filename', 
        type=str,
        help='Path to the quantum chemistry output file to parse'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='chiroptic.txt',
        help='Output file name (default: chiroptic.txt)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Call the parse function with the provided filename
    parse_custom_file(args.filename)

if __name__ == "__main__":
    main()