#!/usr/bin/env python3
import os
from workflow_tools.vasp.vasp_utility import is_spin_polarized, extract_nbands_and_nkpts
from collections import defaultdict

def compress_occupancies(occ_list):
    """
    Compress a list of occupancies using short notation.
    Example: ['1.0', '1.0', '0.5', '0.0', '0.0', '0.0'] -> ['2*1.0', '0.5', '3*0.0']
    """
    if not occ_list:
        return []
    
    compressed = []
    current_val = occ_list[0]
    count = 1
    
    for val in occ_list[1:]:
        if val == current_val:
            count += 1
        else:
            if count > 1:
                compressed.append(f"{count}*{current_val}")
            else:
                compressed.append(current_val)
            current_val = val
            count = 1
    
    # Add the last group
    if count > 1:
        compressed.append(f"{count}*{current_val}")
    else:
        compressed.append(current_val)
    
    return compressed

def extract_occupancy():
    input_file = 'EIGENVAL'
    output_file = 'electron_occupancy'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    nbands, nkpts = extract_nbands_and_nkpts()
    polarized = is_spin_polarized()
    
    if nbands is None or nkpts is None:
        print("Error: Could not extract NBANDS or NKPTS from OUTCAR.")
        return

    ferwe = defaultdict(list)
    ferdo = defaultdict(list)
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
            
            # Standard VASP EIGENVAL:
            # Lines 0-4: System info
            # Line 5: N_elect, N_kpts, N_bands
            # Line 6: Comments/Units (e.g. "Energy (eV)") or empty
            current_line_idx = 7

            for k in range(nkpts):
                # Each k-point block has a header line (coords + weight) and a blank line after
                # This k-point header line is skipped
                current_line_idx += 1 
                
                for b in range(nbands):
                    data = lines[current_line_idx].split()
                    
                    if polarized:
                        # Format: id e_up e_down occ_up occ_down
                        # occ_up is index 3, occ_down is index 4
                        ferwe[k].append(data[3])
                        ferdo[k].append(data[4])
                    else:
                        # Format: id e_eigen occ
                        # occ is index 2
                        ferwe[k].append(data[2])

                    current_line_idx += 1
                # Skip the blank line after each k-point block
                current_line_idx += 1
                    
    except IndexError:
        print("Error parsing file structure. Please check EIGENVAL format.")
        return

    with open(output_file, 'w') as out:
        # Print one kpoint per line, with bands separated by spaces, and k-points separated by newlines
        # For spin-polarized, we will have two lines: one for spin-up and one for spin-down
        for k in range(nkpts):
            # Compress consecutive identical occupancies
            ferwe_compressed = compress_occupancies(ferwe[k])
            ferwe_str = ' '.join(ferwe_compressed)
            if k == 0:
                out.write(f"FERWE = {ferwe_str} \\\n")
            elif k == nkpts - 1:
                out.write(f"{ferwe_str} \n")
            else:
                out.write(f"{ferwe_str} \\\n")
        
        if polarized:
            for k in range(nkpts):
                ferdo_compressed = compress_occupancies(ferdo[k])
                ferdo_str = ' '.join(ferdo_compressed)
                if k == 0:
                    out.write(f"\nFERDO = {ferdo_str} \\\n")
                elif k == nkpts - 1:
                    out.write(f"{ferdo_str} \n")
                else:
                    out.write(f"{ferdo_str} \\\n")

if __name__ == "__main__":
    extract_occupancy()