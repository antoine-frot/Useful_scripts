#!/bin/bash
#==============================================================================
# do_bader.sh - VASP Bader Charge Analysis Workflow
#==============================================================================
# DESCRIPTION:
#   Performs complete Bader charge analysis on VASP charge density files.
#   Automatically detects VASP version and selects the correct AECCAR files.
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

# Detect VASP version
if [ ! -f "VASP_version.txt" ]; then
  echo "Error: VASP_version.txt not found. Please include this file."
  exit 1
fi

# Select AECCAR files depending on version
if grep -q "Vasp6" VASP_version.txt; then
  AECCAR_CORE="AECCAR0"
  AECCAR_TOTAL="AECCAR2"
elif grep -q "Vasp5" VASP_version.txt; then
  AECCAR_CORE="AECCAR0"
  AECCAR_TOTAL="AECCAR1"
else
  echo "Warning: Unknown VASP version '$VASP_VERSION'"
  exit 1
fi

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

# Clean sixth line format issues
awk '{if ((NR!=6)||($1 ~ /[0-9]+/)) print $0}' "$AECCAR_CORE" > A0
awk '{if ((NR!=6)||($1 ~ /[0-9]+/)) print $0}' "$AECCAR_TOTAL" > A2
awk '{if ((NR!=6)||($1 ~ /[0-9]+/)) print $0}' CHGCAR > A3
mv A0 "$AECCAR_CORE"
mv A2 "$AECCAR_TOTAL"
mv A3 CHGCAR

# Combine AECCAR files (core + total/all-electron)
perl "$SCRIPT_DIR/chgsum.pl" "$AECCAR_CORE" "$AECCAR_TOTAL"

# Run Bader analysis on total charge
"$SCRIPT_DIR/bader" CHGCAR -ref CHGCAR_sum
cp ACF.dat ACF_chg.dat

# Run Bader analysis on magnetic charge density
"$SCRIPT_DIR/chgsplit" CHGCAR
"$SCRIPT_DIR/bader" CHGCAR_mag.vasp
cp ACF.dat ACF_mag.dat

# Restore backups and clean up
mv "${AECCAR_CORE}_init" "$AECCAR_CORE"
mv "${AECCAR_TOTAL}_init" "$AECCAR_TOTAL"
mv CHGCAR_init CHGCAR
rm CHGCAR_up* CHGCAR_down*

# Post-processing: summary
python3 "$SCRIPT_DIR/Bader_analyse.py" > Bader_analyse
echo "Bader charge analysis completed. Results in Bader_analyse."