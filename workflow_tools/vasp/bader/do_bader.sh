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

# Clean sixth line format issues
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