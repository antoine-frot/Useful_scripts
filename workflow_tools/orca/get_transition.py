#!/usr/bin/env python3
import argparse
import glob
import os
import re
import fnmatch
from ../get_properties/orca/get_nroots import get_nroots
from ../get_properties/orca/get_HOMO import get_HOMO

threshold_contribution_transition = 0.4  # Variable that chooses which percentage of contribution in the total transition the transition between two orbitals is shown

def parse_transitions(transitions_arg):
    """
    Parse transitions argument into a sorted list of integers.

    Args:
        transitions_arg (str): A string representing transition numbers or ranges (e.g., "1-3,5").

    Returns:
        list: A sorted list of integers representing the transitions.
    """
    transitions = set()
    if not transitions_arg:
        return None
    parts = re.split(r'[, ]+', transitions_arg.strip())
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            transitions.update(range(start, end + 1))
        else:
            if part:  # ignore empty strings
                transitions.add(int(part))
    return sorted(transitions)

def process_file(file_path, transitions, HOMO):
    """
    Process a single file for given transitions.

    Args:
        file_path (str): Path to the file to be processed.
        transitions (list): List of transitions to search for in the file.
        HOMO (int): The HOMO orbital number.
    """
    with open(file_path, 'r') as f:
        content = f.readlines()

    for tr in transitions:
        output = ""
        # Find main transition line
        for line in content:
            if f"0-1A  ->  {tr}-1A" in line:
                output = line.strip()
                break

        if not output:  # Skip if no main transition line found
            continue

        # Find all contributions and track the highest value contribution
        current_state = None
        contributions = []
        max_contribution = None  # Track the contribution with the highest value

        for line in content:
            state_match = re.match(r'STATE\s+(\d+):', line)
            if state_match:
                current_state = int(state_match.group(1))
                continue

            if current_state and current_state == tr:
                trans_match = re.match(
                    r'\s*(\d+)a\s+->\s+(\d+)a\s*:\s*([0-9.]+)',
                    line
                )
                if trans_match:
                    Orbital1, Orbital2, value = trans_match.groups()
                    Orbital1 = int(Orbital1)
                    Orbital2 = int(Orbital2)
                    value_float = float(value)

                    # Convert Orbital1 to HOMO/LUMO notation
                    if Orbital1 == HOMO:
                        Orbital1 = "HOMO"
                    elif Orbital1 == HOMO + 1:
                        Orbital1 = "LUMO"
                    elif Orbital1 < HOMO:
                        Orbital1 = f"HOMO{Orbital1 - HOMO:+d}"
                    else:
                        Orbital1 = f"LUMO{Orbital1 - HOMO - 1:+d}"

                    # Convert Orbital2 similarly
                    if Orbital2 == HOMO:
                        Orbital2 = "HOMO"
                    elif Orbital2 == HOMO + 1:
                        Orbital2 = "LUMO"
                    elif Orbital2 < HOMO:
                        Orbital2 = f"HOMO{Orbital2 - HOMO:+d}"
                    else:
                        Orbital2 = f"LUMO{Orbital2 - HOMO - 1:+d}"

                    # Track the contribution with the highest value
                    if max_contribution is None or value_float > max_contribution[2]:
                        max_contribution = (Orbital1, Orbital2, value_float)

                    # Add to contributions if above threshold
                    if value_float > threshold_contribution_transition:
                        contributions.append(f"| {Orbital1} -> {Orbital2} : {value_float:.6f}")

        # If no contributions meet the threshold, include the highest value contribution
        if not contributions and max_contribution is not None:
            Orbital1, Orbital2, value_float = max_contribution
            contributions.append(f"| {Orbital1} -> {Orbital2} : {value_float:.6f}")

        # Print the output with contributions
        if contributions:
            print(f"{output} {' '.join(contributions)}")
        else:
            print(output)

def main():
    """
    Main function to search transition patterns in computational chemistry outputs.

    This script processes computational chemistry output files to find and display
    transition patterns based on specified methods and molecule patterns.

    Usage:
        python script.py [transitions] --methods METHODS --molecule MOLECULE

    Args:
        transitions (str, optional): Transition numbers/ranges (e.g., "1-3,5").
        --methods, -m (str, required): Comma-separated list of methods (ABS/FLUO base or specific ABS@*/FLUO@*).
        --molecule, -M (str, optional): Comma-separated list of molecule name patterns (default: Boranil*).
    """
    parser = argparse.ArgumentParser(description='Search transition patterns in computational chemistry outputs')
    parser.add_argument('transitions', nargs='?', default=None,
                        help='Transition numbers/ranges (e.g., "1-3,5")')
    parser.add_argument('--methods', '-m', nargs='?', type=str, required=True,
                        help='Comma-separated list of methods (ABS/FLUO base or specific ABS@*/FLUO@*)')
    parser.add_argument('--molecule', '-M', type=str, default='Boranil*',
                        help='Comma-separated list of molecule name patterns (default: Boranil*)')

    args = parser.parse_args()

    # Validate methods
    methods = [m.strip() for m in args.methods.split(',')]
    if not methods:
        raise ValueError("No methods specified")
    
    # Parse transitions
    transitions = parse_transitions(args.transitions)
    
    # Parse molecule patterns (NEW: handle comma-separated molecule patterns)
    molecule_patterns = [m.strip() for m in args.molecule.split(',')]
    
    # Find matching molecules from all patterns
    molecules = []
    for pattern in molecule_patterns:
        matches = glob.glob(pattern)
        if matches:
            molecules.extend(matches)
    
    if not molecules:
        patterns_str = ', '.join(molecule_patterns)
        raise FileNotFoundError(f"No molecules found matching patterns: {patterns_str}")

    # Sort molecules alphabetically by their basename and remove duplicates
    molecules = sorted(set(molecules), key=lambda x: os.path.basename(x))

    # Search through files
    print("""
--------------------------------------------------------------------------------------------------
                   ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS
--------------------------------------------------------------------------------------------------
   Transition      Energy     Energy  Wavelength fosc(D2)      D2        DX        DY        DZ
                    (eV)      (cm-1)    (nm)                 (au**2)    (au)      (au)      (au)
--------------------------------------------------------------------------------------------------
""")
    for mol_path in molecules:
        mol_name = os.path.basename(mol_path)

        # Find available methods for this molecule
        method_dirs = glob.glob(os.path.join(mol_path, f"{mol_name}-*"))
        existing_methods = []
        for md in method_dirs:
            if os.path.isdir(md):
                dir_name = os.path.basename(md)
                parts = dir_name.split('-', 1)
                if len(parts) == 2:
                    existing_methods.append(parts[1])

        # Expand user methods to patterns
        method_patterns = []
        for user_method in methods:
            if user_method in ['ABS', 'FLUO']:
                method_patterns.append(f"OPT[GE]S@*-{user_method}@*")
            else:
                method_patterns.append(user_method)

        # Find matching methods
        selected_methods = set()
        for pattern in method_patterns:
            for em in existing_methods:
                if fnmatch.fnmatch(em, pattern):
                    selected_methods.add(em)
        
        # Process matching methods
        for method in selected_methods:
            out_dir = os.path.join(mol_path, f"{mol_name}-{method}")
            out_file = os.path.join(out_dir, f"{mol_name}-{method}.out")

            if not os.path.isfile(out_file):
                print(f"{out_file} not found.")
                continue

            # Determine transitions to search for this file
            file_transitions = transitions if transitions else []
            if not file_transitions:
                nroots = get_nroots(out_file)
                if nroots:
                    file_transitions = range(1, nroots + 1)

            if len(molecules) * len(selected_methods) > 1:
                print(f"\nFound in {os.path.basename(out_dir)}:")

            HOMO = get_HOMO(out_file)
            process_file(out_file, file_transitions, HOMO)

if __name__ == "__main__":
    main()

