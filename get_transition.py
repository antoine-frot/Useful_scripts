#!/usr/bin/env python3
import argparse
import glob
import os
import re
import fnmatch
from get_nroots import get_nroots
from get_HOMO import get_HOMO

threshhold_contribution_transition = 0.25 # Variable that choose which pourcentage of contribution in the total transition the transition between two orbitals is shown 

def parse_transitions(transitions_arg):
    """Parse transitions argument into a sorted list of integers"""
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
    """Process a single file for given transitions"""
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
            
        # Find all contributions above threshold
        current_state = None
        contributions = []
        
        for line in content:
            state_match = re.match(r'STATE\s+(\d+):', line)
            if state_match:
                current_state = int(state_match.group(1))
                continue
                
            if current_state and current_state == tr:
                trans_match = re.match(
                    r'\s*(\d+)a -> (\d+)a\s*:\s*([0-9.]+)\s*\(c=.*\)',
                    line
                )
                if trans_match:
                    Orbital1, Orbital2, value = trans_match.groups()
                    Orbital1 = int(Orbital1)
                    Orbital2 = int(Orbital2)
                    value_float = float(value)

                    if Orbital1 == HOMO:
                        Orbital1 = "HOMO"
                    elif Orbital1 == HOMO + 1 :
                        Orbital1 = "LUMO"
                    elif Orbital1 < HOMO:
                        Orbital1 = f"HOMO{Orbital1 - HOMO:+d}"
                    elif Orbital1 > HOMO + 1 :
                        Orbital1 = f"LUMO{Orbital1 - HOMO - 1:+d}"
                    if Orbital2 == HOMO:
                        Orbital2 = "HOMO"
                    elif Orbital2 == HOMO + 1 :
                        Orbital2 = "LUMO"
                    elif Orbital2 < HOMO:
                        Orbital2 = f"HOMO{Orbital2 - HOMO:+d}"
                    elif Orbital2 > HOMO + 1 :
                        Orbital2 = f"LUMO{Orbital2 - HOMO - 1:+d}"

                    if value_float > threshhold_contribution_transition:
                        contributions.append(f"| {Orbital1} -> {Orbital2} : {value_float:.6f}")
        
        # Print combined output with all contributions on same line
        if contributions:
            print(f"{output} {' '.join(contributions)}")
        else:
            print(output)

def main():
    parser = argparse.ArgumentParser(description='Search transition patterns in computational chemistry outputs')
    parser.add_argument('transitions', nargs='?', default=None,
                      help='Transition numbers/ranges (e.g., "1-3,5")')
    parser.add_argument('methods', type=str,
                      help='Comma-separated list of methods (ABS/FLUO base or specific ABS@*/FLUO@*)')
    parser.add_argument('molecule', type=str, nargs='?', default='Boranil*',
                      help='Molecule name pattern (default: Boranil*)')
    
    args = parser.parse_args()

    # Validate methods
    methods = [m.strip() for m in args.methods.split(',')]
    for method in methods:
        if not (method in ['ABS', 'FLUO'] or 
                method.startswith('ABS@') or 
                method.startswith('FLUO@')):
            raise ValueError(f"Invalid method '{method}': Must be ABS/FLUO or start with ABS@/FLUO@")

    # Parse transitions
    transitions = parse_transitions(args.transitions)

    # Find matching molecules
    molecules = glob.glob(args.molecule)
    if not molecules:
        raise FileNotFoundError(f"No molecules found matching pattern: {args.molecule}")

    # Sort molecules alphabetically by their basename
    molecules = sorted(molecules, key=lambda x: os.path.basename(x))

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
                method_patterns.append(f"{user_method}@*")
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
                continue

            # Determine transitions to search for this file
            file_transitions = transitions if transitions else []
            if not file_transitions:
                nroots = get_nroots(out_file)
                if nroots:
                    file_transitions = range(1, nroots + 1)

            print(f"\nFound in {os.path.basename(out_dir)}:")
            HOMO = get_HOMO(out_file)
            process_file(out_file, file_transitions, HOMO)

if __name__ == "__main__":
    main()
