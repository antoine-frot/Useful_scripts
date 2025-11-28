#!/usr/bin/env python3
import sys
import os
import argparse
import numpy as np

def split_chgcar(input_file, mag=False):
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    print(f"Processing {input_file}...")

    try:
        with open(input_file, 'r') as f:
            header_lines = []

            # Skip the headers
            for _ in range(9):
                line = f.readline()
                header_lines.append(line)
            # --- 1. Read the Structure Header ---
            # Read until we find the Grid Dimensions line (3 integers)
            # The structure part usually has a fixed format, but atom counts vary.
            while True:
                line = f.readline()
                header_lines.append(line)
                parts = line.split()
                if len(parts) == 3:
                    try:
                        # Check if line contains 3 integers (NGX, NGY, NGZ)
                        ng_x, ng_y, ng_z = map(int, parts)
                        # If we succeed, break, this is the start of the data
                        break
                    except ValueError:
                        continue

            grid_size = ng_x * ng_y * ng_z
            print(f"Grid detected: {ng_x} x {ng_y} x {ng_z} ({grid_size} points)")

            # --- 2. Read Total Charge (Spin Up + Spin Down) ---
            # We read the exact number of float values required for the grid
            # Using numpy fromfile/fromstring is faster, but we are in a stream.
            # We use a scanner approach.

            data_total = []
            values_read = 0

            # Read chunks until we have all grid points
            while values_read < grid_size:
                line_data = f.readline().split()
                data_total.extend([float(x) for x in line_data])
                values_read += len(line_data)

            # Convert to numpy array for math
            np_total = np.array(data_total)

            # --- 3. Find the Magnetization Block ---
            # Between Total and Magnetization, there might be "augmentation occupancies"
            # We skip lines until we see the grid dimensions again

            lines_between = [] # We might want to keep augmentation lines, but for strict UP/DW split
                               # we usually just want the grid. VESTA handles clean grid files better.
                               # However, to be safe, we will just look for the next grid line.

            found_mag = False
            while True:
                pos = f.tell() # Save position to peek
                line = f.readline()
                if not line:
                    break # End of file

                parts = line.split()
                if len(parts) == 3:
                    try:
                        nx, ny, nz = map(int, parts)
                        if nx == ng_x and ny == ng_y and nz == ng_z:
                            found_mag = True
                            break
                    except ValueError:
                        pass

            if not found_mag:
                print("Error: Could not find Spin Magnetization block. Is this ISPIN=2?")
                return

            # --- 4. Read Magnetization (Spin Up - Spin Down) ---
            data_mag = []
            values_read = 0
            while values_read < grid_size:
                line_data = f.readline().split()
                data_mag.extend([float(x) for x in line_data])
                values_read += len(line_data)

            np_mag = np.array(data_mag)

            # --- 5. Calculate Up and Down Channels ---
            # Total = Up + Down
            # Mag   = Up - Down
            # Up    = (Total + Mag) / 2
            # Down  = (Total - Mag) / 2

            np_up = (np_total + np_mag) / 2.0
            np_down = (np_total - np_mag) / 2.0

            # --- 6. Write Outputs ---
            base_name = os.path.basename(input_file)
            if '.vasp' in base_name:
                print(F"Warning: {base_name} has .vasp extension.")
                base_name = base_name.replace('.vasp', '')
                print(f"Output name will be {base_name}_up.vasp and {base_name}_dw.vasp")
                response = input("Do you want to continue? (y/n): ")
                if response.lower() != 'y':
                    return
            name_up = f"{base_name}_up.vasp"
            name_dw = f"{base_name}_dw.vasp"

            write_vasp(name_up, header_lines, np_up)
            write_vasp(name_dw, header_lines, np_down)
            if mag:
                name_mag = f"{base_name}_mag.vasp"
                write_vasp(name_mag, header_lines, np_mag)
            print(f"Done! Created:\n  - {name_up}\n  - {name_dw}")
            if mag:
                print(f"  - {name_mag}") # type: ignore


    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def write_vasp(filename, header_lines, data):
    """ Writes the VASP formatted file """
    with open(filename, 'w') as f:
        # Write Header
        f.writelines(header_lines)

        # Write Data
        # VASP usually formats data in 5 columns, scientific notation
        count = 0
        for val in data:
            f.write(f" {val:17.11E}")
            count += 1
            if count % 5 == 0:
                f.write("\n")

        # Add a newline at the end if the last line wasn't complete
        if count % 5 != 0:
            f.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split CHGCAR-like files (CHGCAR, PARCHG, ...) into spin-up and spin-down VASP files.")
    parser.add_argument("files", nargs="+", help="List of CHGCAR-like files (CHGCAR, PARCHG, ...) to process")
    parser.add_argument("-m", "--mag", action="store_true",
                        help="Produce the magnetization file (UP - DW)")
    args = parser.parse_args()

    for arg in args.files:
        split_chgcar(arg, mag=args.mag)