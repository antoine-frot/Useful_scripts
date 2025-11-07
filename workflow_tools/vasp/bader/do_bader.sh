#!/bin/bash
#==============================================================================
# do_bader.sh - VASP Bader Charge Analysis Workflow
#==============================================================================
# DESCRIPTION:
#   Performs complete Bader charge analysis on VASP charge density files.
#   This script orchestrates the entire workflow from preprocessing VASP
#   output files to generating final analysis results.
#
# USAGE:
#   do_bader
#
# REQUIREMENTS:
#   - VASP output files in current directory: AECCAR0, AECCAR2, CHGCAR, CONTCAR
#   - Auxiliary tools: bader, chgsplit, chgsum.pl, Bader_analyse.py
#
# OUTPUT FILES:
#   - ACF_chg.dat: Bader charges for total density
#   - ACF_mag.dat: Bader charges for magnetic density
#   - Bader_analyse: Summary analysis report
#
#==============================================================================
set -e

# Get the directory where this script is actually located (resolve symlinks)
SOURCE="${BASH_SOURCE[0]}"
# Resolve $SOURCE until the file is no longer a symlink
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # Transform $SOURCE into an absolute path
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

cp AECCAR0 AECCAR0_init
cp AECCAR2 AECCAR02_init
cp CHGCAR CHGCAR_init
#awk '{if(NR!=6) print $0}' AECCAR0 > A0
#awk '{if(NR!=6) print $0}' AECCAR2 > A2
#awk '{if(NR!=6) print $0}' CHGCAR > A3
awk '{if ((NR!=6)||($1 ~ /[0-9]+/)) print $0}' AECCAR2 > A2
awk '{if ((NR!=6)||($1 ~ /[0-9]+/)) print $0}' CHGCAR > A3
awk '{if ((NR!=6)||($1 ~ /[0-9]+/)) print $0}' AECCAR0 > A0
mv A0 AECCAR0
mv A2 AECCAR2
mv A3 CHGCAR
perl "$SCRIPT_DIR/chgsum.pl" AECCAR0 AECCAR2
"$SCRIPT_DIR/bader" CHGCAR -ref CHGCAR_sum
cp ACF.dat ACF_chg.dat
"$SCRIPT_DIR/chgsplit" CHGCAR
"$SCRIPT_DIR/bader" CHGCAR_mag.vasp
cp ACF.dat ACF_mag.dat
mv AECCAR0_init AECCAR0
mv AECCAR02_init AECCAR2
mv CHGCAR_init CHGCAR
rm CHGCAR_up* CHGCAR_down*
python3 "$SCRIPT_DIR/Bader_analyse.py" > Bader_analyse

