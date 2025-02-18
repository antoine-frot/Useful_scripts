#!/bin/bash
#SBATCH -J Orca
#SBATCH -p Lake,Cascade
#SBATCH -o %j.out
#SBATCH -e %j.err
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --mem=100G  # If you do not calculate Hessian matrix, 1000 is probably enough.
#SBATCH --cpus-per-task=1
#SBATCH --time=7-23:00:00
#

module purge
module use /applis/PSMN/debian11/Lake/modules/all/
module use /Xnfs/chimie/debian11/modules/
module load orca/6.0.1_openmpi416
 
input="$1"
output=$(basename "${input}" .inp).out
 
SCRATCHDIR=`mktemp -d`

HOMEDIR="$SLURM_SUBMIT_DIR"
 
cd ${HOMEDIR} || { echo "cannot cd to ${HOMEDIR}"; exit 1; }
cp "${input}" *.xyz *.bas *.pc "${SCRATCHDIR}" 2>/dev/null
cd  "${SCRATCHDIR}" || { echo "cannot cd to ${SCRATCHDIR}"; exit 1; }
orca_calc_done=0
(/Xnfs/chimie/debian11/orca/orca_6_0_1/orca "${input}" > "${HOMEDIR}/${output}"; orca_calc_done=1; echo "all done" ) &
while [ $orca_calc_done == 0 ]
do
    cp  *.gbw *.hess *.xyz *.interp *.nbo ${HOMEDIR}/ 2>/dev/null
    sleep 30
done
echo "${input%.inp}" > /home/afrot/Stage2025Tangui/Submited.txt
rm -rf "${SCRATCHDIR}"


