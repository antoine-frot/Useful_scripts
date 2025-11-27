#!/bin/bash
#==============================================================================
# do_bader.sh - VASP Bader Charge Analysis Workflow
#==============================================================================
# DESCRIPTION:
#   Performs complete Bader charge analysis on VASP charge density files.
#   Automatically detects VASP version and selects the correct AECCAR files.
#   Comes from the Henkelman Bader tools and Marie-Liesse Doublet script.
#
# USAGE:
#   Run in directory containing: AECCAR*, CHGCAR, CONTCAR/POSCAR, VASP_version.txt
#   ./do_bader.sh
#
# OUTPUT:
#   - ACF_chg.dat, ACF_mag.dat (raw Bader results)
#   - Bader_analyse (summary report)
#==============================================================================
set -e

# Get script directory (resolve symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

AECCAR_CORE="AECCAR0"
AECCAR_TOTAL="AECCAR2"

# Check required files exist
for file in "$AECCAR_CORE" "$AECCAR_TOTAL" CHGCAR; do
  if [ ! -f "$file" ]; then
    echo "Error: Required file ($file) not found in current directory."
    echo "Make sure AECCAR* and CHGCAR are present."
    exit 1
  fi
done

# Backup and preprocessing
cp "$AECCAR_CORE" "${AECCAR_CORE}_init"
cp "$AECCAR_TOTAL" "${AECCAR_TOTAL}_init"
cp CHGCAR CHGCAR_init

# Clean sixth line (Atomic species) because Bader tools work with VASP4 output format that does not have this line
awk '{if ((NR!=6)||($1 ~ /[0-9]+/)) print $0}' "$AECCAR_CORE" > A0
awk '{if ((NR!=6)||($1 ~ /[0-9]+/)) print $0}' "$AECCAR_TOTAL" > A2
awk '{if ((NR!=6)||($1 ~ /[0-9]+/)) print $0}' CHGCAR > A3
mv A0 "$AECCAR_CORE"
mv A2 "$AECCAR_TOTAL"
mv A3 CHGCAR

# Combine AECCAR files (core + total/all-electron)
perl "$SCRIPT_DIR/chgsum.pl" "$AECCAR_CORE" "$AECCAR_TOTAL" # create CHGCAR_sum

# Run Bader analysis on total charge
"$SCRIPT_DIR/bader" CHGCAR -ref CHGCAR_sum
mv ACF.dat ACF_chg.dat
tmpfile="$(mktemp)"
{
  echo "# Bader Analysis of Charge Density"
  printf '%0.s-' {1..81}
  echo
  cat ACF_chg.dat
} > "$tmpfile" && mv "$tmpfile" ACF_chg.dat

# Run Bader analysis on magnetic charge density
"$SCRIPT_DIR/chgsplit" CHGCAR
"$SCRIPT_DIR/bader" CHGCAR_mag.vasp -ref CHGCAR_sum
mv ACF.dat ACF_mag.dat
tmpfile="$(mktemp)"
{
  echo "# Bader Analysis of Magnetization Density"
  printf '%0.s-' {1..81}
  echo
  cat ACF_mag.dat
} > "$tmpfile" && mv "$tmpfile" ACF_mag.dat
sed -i 's/CHARGE/MAGNET/' ACF_mag.dat
sed -i 's/NUMBER OF ELECTRONS/TOTAL MAGNETIZATION/' ACF_mag.dat

# Restore backups and clean up
mv "${AECCAR_CORE}_init" "$AECCAR_CORE"
mv "${AECCAR_TOTAL}_init" "$AECCAR_TOTAL"
mv CHGCAR_init CHGCAR
mv CHGCAR_mag.vasp CHGCAR_mag
rm CHGCAR_up* CHGCAR_down* CHGCAR_sum

# Post-processing: summary
echo ""
if ! python3 "$SCRIPT_DIR/Bader_analyse.py" > Bader_analyse; then
    echo "ERROR: Bader analysis failed during post-processing."
    echo "Check the Bader_analyse file for error details."
    echo "Raw Bader results are still available in ACF_chg.dat and ACF_mag.dat"
fi
echo "Files generated: " 
echo "ACF_chg.dat charge density Bader analysis"
echo "ACF_mag.dat magnetic charge density Bader analysis"
echo "Bader_analyse summary of Bader analysis results"
echo "CHGCAR_mag magnetic charge density file"
echo "Additional files:"
echo "BCF.dat topological properties of the Bader volumes"
echo "AVF.dat volume files for each Bader volume"
echo "Reminder:"
echo "- AECCAR0 core charge density."
echo "- AECCAR1 smooth pseudo valence charge density."
echo "- AECCAR2 valence all-electron density (pseudo valence + PAW augmentation)."

# Enhance the format of ACF_chg.dat and ACF_mag.dat files
python3 - <<END_PYTHON
import os

def get_atom_list(poscar_path="POSCAR"):
    """
    Reads POSCAR/CONTCAR to get the list of element names corresponding to atoms.
    Assumes VASP 5 format (element symbols on line 6).
    """
    if not os.path.exists(poscar_path):
        # Try CONTCAR if POSCAR is missing
        if poscar_path == "POSCAR" and os.path.exists("CONTCAR"):
            poscar_path = "CONTCAR"
        else:
            print(f"Error: {poscar_path} not found. Cannot determine atom names.")
            return []

    try:
        with open(poscar_path, 'r') as f:
            lines = f.readlines()
            
            # VASP 5: Line 6 contains element symbols, Line 7 contains counts
            # (Indices are 5 and 6 because Python is 0-indexed)
            elements = lines[5].split()
            counts_line = lines[6].split()
            
            # check if line 5 is actually elements (VASP 5) or numbers (VASP 4)
            if elements[0].isdigit():
                print("Error: POSCAR format appears to be VASP 4 (no element names).")
                print("Please verify POSCAR has element symbols on the 6th line.")
                return []

            counts = [int(x) for x in counts_line]
            
            atom_list = []
            for elem, count in zip(elements, counts):
                atom_list.extend([elem] * count)
                
            return atom_list
    except Exception as e:
        print(f"Error reading geometry file: {e}")
        return []

def process_acf_file(filename, atom_list):
    """
    Reads an ACF file, inserts the Ion name, and writes a new file.
    """
    if not os.path.exists(filename):
        print(f"Skipping {filename} (not found).")
        return

    output_filename = filename.replace(".dat", "_labeled.dat")
    
    with open(filename, 'r') as f_in, open(output_filename, 'w') as f_out:
        lines = f_in.readlines()
        
        for line in lines:
            parts = line.split()
            
            # 1. Handle Empty Lines
            if not parts:
                f_out.write(line)
                continue

            # 2. Handle The Header Line
            if "X" in parts and "Y" in parts and "Z" in parts:
                # Replace the header with the new format including 'Ion'
                f_out.write("    #    Ion         X           Y           Z        CHARGE     MIN DIST    ATOMIC VOL\n")
                continue

            # 3. Handle Separator Lines (dashes)
            if "-----" in line:
                f_out.write(92*"-" + "\n")
                continue

            # 4. Handle Data Lines (Start with a number)
            if parts[0].isdigit():
                try:
                    index = int(parts[0])
                    # Get element name (index - 1 because list is 0-based)
                    if index <= len(atom_list):
                        element = atom_list[index - 1]
                    else:
                        element = "??"

                    # Format the line strictly to match user request
                    # {Index} {Element} {X} {Y} {Z} {Charge} {Dist} {Vol}
                    formatted_line = (
                        f"{index:>5}    {element:<4} "
                        f"{parts[1]:>10}  {parts[2]:>10}  {parts[3]:>10}  "
                        f"{parts[4]:>10}  {parts[5]:>10}  {parts[6]:>10}\n"
                    )
                    f_out.write(formatted_line)
                except ValueError:
                    # If parts[0] isn't a clean integer, just write line as is
                    f_out.write(line)
            
            # 5. Handle Footer lines (NUMBER OF ELECTRONS etc)
            else:
                f_out.write(line)

if __name__ == "__main__":
    atoms = get_atom_list("POSCAR")
    if atoms:
        process_acf_file("ACF_chg.dat", atoms)
        process_acf_file("ACF_mag.dat", atoms)
        
        # Also try standard ACF.dat just in case
        if os.path.exists("ACF.dat"):
            process_acf_file("ACF.dat", atoms)
END_PYTHON