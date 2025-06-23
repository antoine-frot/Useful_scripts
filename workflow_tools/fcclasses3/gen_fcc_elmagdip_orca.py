#!/usr/bin/env python3
"""
Script to create eldip and magdip files for fcclasses from an ORCA calculation.
"""

import argparse
import sys
from get_properties.electronic_transition_parser import parse_orca_format

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Process ORCA photon absorption and emission calculation files'
    )

    parser.add_argument(
        'absorption_file',
        help='ORCA photon absorption calculation file'
    )

    parser.add_argument(
        'emission_file',
        help='ORCA photon emission calculation file'
    )

    parser.add_argument(
        '--velocity',
        action='store_true',
        help='Set gauge to velocity (uses PX PY PZ components). Default is length gauge (uses DX DY DZ components)'
    )

    args = parser.parse_args()

    try:
        # Parse both input files
        absorption_data = parse_orca_format(args.absorption_file)
        emission_data = parse_orca_format(args.emission_file)

        # Determine which electric dipole components to use based on gauge
        if args.velocity:
            # Velocity gauge - use PX, PY, PZ
            elec_components = ['PX', 'PY', 'PZ']
        else:
            # Length gauge (default) - use DX, DY, DZ
            elec_components = ['DX', 'DY', 'DZ']

        # Write electric dipole components to eldip file
        with open('eldip', 'w') as f:
            # First line: absorption data
            absorption_values = [str(absorption_data.get(comp, 0.0)) for comp in elec_components]
            f.write(' '.join(absorption_values) + '\n')

            # Second line: emission data
            emission_values = [str(emission_data.get(comp, 0.0)) for comp in elec_components]
            f.write(' '.join(emission_values) + '\n')

        # Write magnetic dipole components to magdip file
        mag_components = ['MX', 'MY', 'MZ']
        with open('magdip', 'w') as f:
            # First line: absorption data
            absorption_mag_values = [str(absorption_data.get(comp, 0.0)) for comp in mag_components]
            f.write(' '.join(absorption_mag_values) + '\n')

            # Second line: emission data
            emission_mag_values = [str(emission_data.get(comp, 0.0)) for comp in mag_components]
            f.write(' '.join(emission_mag_values) + '\n')

        print("Output files created: eldip, magdip")
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing files: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
