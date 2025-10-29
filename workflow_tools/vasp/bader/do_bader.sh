#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

