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

choose_vasp_version() {
  while true; do 
    read -p "Please enter VASP version (5 or 6): " user_vasp_version
    if [ "$user_vasp_version" = "6" ]; then
      echo "Vasp6"
      return
    elif [ "$user_vasp_version" = "5" ]; then
      echo "Vasp5"
      return
    else
      echo "Error: Invalid VASP version entered. Please enter 5 or 6."
    fi
  done
}
# Get script directory (resolve symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

# Make AECCAR files VESTA readable
for AECCAR in AECCAR0 AECCAR1 AECCAR2; do
  if [ -f "$AECCAR" ]; then
    cp "$AECCAR" "${AECCAR}.vasp"
  fi
done

# Select AECCAR files depending on version
if [ ! -f "VASP_version.txt" ]; then
  echo "VASP_version.txt not found."
elif grep -q "Vasp6" VASP_version.txt; then
  VASP_VERSION="Vasp6"
elif grep -q "Vasp5" VASP_version.txt; then
  VASP_VERSION="Vasp5"
else
  VASP_VERSION_READ=$(cat VASP_version.txt)
  echo "Warning: Unknown VASP version: '$VASP_VERSION_READ'. Expected 'Vasp5' or 'Vasp6' in VASP_version.txt."
fi

if [ -z "$VASP_VERSION" ]; then
  VASP_VERSION=$(choose_vasp_version)
fi

if [ "$VASP_VERSION" = "Vasp6" ]; then
    AECCAR_CORE="AECCAR0"
    AECCAR_TOTAL="AECCAR2"
elif [ "$VASP_VERSION" = "Vasp5" ]; then
    AECCAR_CORE="AECCAR0"
    AECCAR_TOTAL="AECCAR1"
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
perl "$SCRIPT_DIR/chgsum.pl" "$AECCAR_CORE" "$AECCAR_TOTAL" # create CHGCAR_sum

# Run Bader analysis on total charge
"$SCRIPT_DIR/bader" CHGCAR -ref CHGCAR_sum
mv ACF.dat ACF_chg.dat
printf ' %0.s-' {1..81} | cat - ACF_chg.dat > tmp && mv tmp ACF_chg.dat
sed -i '1i # Bader Analysis of Charge Density' ACF_chg.dat

# Run Bader analysis on magnetic charge density
"$SCRIPT_DIR/chgsplit" CHGCAR
"$SCRIPT_DIR/bader" CHGCAR_mag.vasp
mv ACF.dat ACF_mag.dat
printf ' %0.s-' {1..81} | cat - ACF_mag.dat > tmp && mv tmp ACF_mag.dat
sed -i '1i # Bader Analysis of Magnetization Density' ACF_mag.dat
sed -i 's/CHARGE/MAGNET/g' ACF_mag.dat
sed -i 's/NUMBER OF ELECTRONS/TOTAL MAGNETIZATION/' ACF_mag.dat

# Restore backups and clean up
mv "${AECCAR_CORE}_init" "$AECCAR_CORE"
mv "${AECCAR_TOTAL}_init" "$AECCAR_TOTAL"
mv CHGCAR_init CHGCAR
mv CHGCAR_mag.vasp CHGCAR_mag
rm CHGCAR_up* CHGCAR_down* CHGCAR_sum

# Post-processing: summary
python3 "$SCRIPT_DIR/Bader_analyse.py" > Bader_analyse
echo ""
echo "Files generated: " 
echo "ACF_chg.dat charge density Bader analysis"
echo "ACF_mag.dat magnetic charge density Bader analysis"
echo "Bader_analyse summary of Bader analysis results"
echo "CHGCAR_mag magnetic charge density file"
echo "Additional files:"
echo "BCF.dat topological properties of the Bader volumes"
echo "AVF.dat volume files for each Bader volume"
echo "Reminder:"
if [ "$VASP_VERSION" = "Vasp6" ]; then
  echo "- AECCAR0 core charge density."
  echo "- AECCAR1 smooth pseudo valence charge density."
  echo "- AECCAR2 valence all-electron density (pseudo valence + PAW augmentation)."
elif [ "$VASP_VERSION" = "Vasp5" ]; then
  echo "- AECCAR0 core charge density."
  echo "- AECCAR1 valence all-electron density (pseudo valence + PAW augmentation)."
fi