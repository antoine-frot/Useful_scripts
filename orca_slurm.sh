#!/bin/bash
#SBATCH -J Orca
#SBATCH -p Lake,Cascade
#SBATCH -o %j.out
#SBATCH -e %j.err
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --mem=100G
#SBATCH --cpus-per-task=1
#SBATCH --time=7-23:00:00

module purge
module use /applis/PSMN/debian11/Lake/modules/all/
module use /Xnfs/chimie/debian11/modules/
module load orca/6.0.1_openmpi416

input="$1"
output=$(basename "${input}" .inp).out

SCRATCHDIR=$(mktemp -d)
HOMEDIR="$SLURM_SUBMIT_DIR"

# Copy input files to scratch directory
cd "${HOMEDIR}" || { echo "cannot cd to ${HOMEDIR}"; exit 1; }
cp "${input}" *.xyz *.bas *.pc *_use.gbw "${SCRATCHDIR}" 2>/dev/null
cd "${SCRATCHDIR}" || { echo "cannot cd to ${SCRATCHDIR}"; exit 1; }

# Initialize ORCA completion flag
orca_calc_done=0
orca_isdone="${SCRATCHDIR}/${SLURM_JOB_ID}.isdone"
echo "$orca_calc_done" > "$orca_isdone"

echo " "
echo "### Calling ORCA command ..."
echo " "

# Run ORCA in the background
(/Xnfs/chimie/debian11/orca/orca_6_0_1/orca "${input}" > "${HOMEDIR}/${output}" 2>&1; orca_calc_done=1; echo "$orca_calc_done" > "$orca_isdone"; echo "all done") &

# Periodically copy output files from scratch to home directory
while [ "$orca_calc_done" -eq 0 ]
do
  sleep 60
  orca_calc_done=$(<"$orca_isdone")
  cp *.gbw *.hess *.xyz *.interp *.nbo "${HOMEDIR}/" 2>/dev/null
done

# Ensure all files are copied after the job finishes
cp *.gbw *.hess *.xyz *.interp *.nbo "${HOMEDIR}/" 2>/dev/null

# Append to Submited.txt
echo "${input%.inp}" >> /home/afrot/Stage2025Tangui/Submited.txt

# Clean up scratch directory
rm -rf "${SCRATCHDIR}"

echo "ORCA calculation completed successfully."
