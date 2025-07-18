#!/bin/bash
#SBATCH -p Lake,Cascade
#SBATCH -o %j.out
#SBATCH -e %j.err
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --time=7-23:00:00

start=$(date +%s)
echo "START_TIME           = `date +'%y-%m-%d %H:%M:%S'`"

echo " "
echo "===== SLURM JOB INFORMATION ====="
echo "Job ID: $SLURM_JOB_ID"
echo "Job Name: $SLURM_JOB_NAME"
echo "Node List: $SLURM_JOB_NODELIST"
echo "Number of Nodes: $SLURM_JOB_NUM_NODES"
echo "Number of Tasks: $SLURM_NTASKS"
echo "Number of CPUs per Task: $SLURM_CPUS_PER_TASK"
echo "Memory Requested per Node: $SLURM_MEM_PER_NODE"
echo "Memory Requested per CPU: $SLURM_MEM_PER_CPU"
echo "Partition: $SLURM_JOB_PARTITION"
echo "Submit Directory: $SLURM_SUBMIT_DIR"
echo "Submit Host: $SLURM_SUBMIT_HOST"
#echo "Allocated GPUs: $SLURM_GPUS"
echo "================================="
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
(/Xnfs/chimie/debian11/orca/orca_6_0_1/orca "${input}" > "${HOMEDIR}/${output}" 2>&1; orca_calc_done=1; echo "$orca_calc_done" > "$orca_isdone") &

# Periodically copy output files from scratch to home directory
while [ "$orca_calc_done" -eq 0 ]
do
  sleep 60
  orca_calc_done=$(<"$orca_isdone")
  cp *.engrad *.nto *.gbw *.hess *.xyz *.interp *.nbo FILE.47 *.densities *.trj *.cis *.densitiesinfo *.loc *.mdcip *.S "${HOMEDIR}/" 2>/dev/null
done

# Ensure all files are copied after the job finishes
cp *.engrad *.nto *.gbw *.hess *.xyz *.interp *.nbo FILE.47 *.densities *.trj *.cis *.densitiesinfo *.loc *.mdcip *.S "${HOMEDIR}/" 2>/dev/null

#Check if the calculation terminated normally and write it in the ouput and Submited file
if head -n 1 "${input}" | grep -iq "opt"; then
    search_pattern="HURRAY"
else
    search_pattern="ORCA TERMINATED NORMALLY"
fi

if grep -iq "$search_pattern" "${HOMEDIR}/${output}"; then
    echo "HURRAY: ${input%.inp}" >> /home/afrot/Stage2025Tangui/Submited.txt
    echo "Calculation terminated normally."
else
    echo "ERROR: ${input%.inp}" >> /home/afrot/Stage2025Tangui/Submited.txt
    echo "Calculation terminated ABnormally."
fi

# Clean up scratch directory
rm -vrf "${SCRATCHDIR}"

end=$(date +%s)
echo "END_TIME           = `date +'%y-%m-%d %H:%M:%S'`"
echo " "
echo "### Calculate duration ..."
echo " "
diff=$[end-start]
if [ $diff -lt 60 ]; then
    echo "Runtime (approx.): $diff secs"
elif [ $diff -lt 3600 ]; then
    echo "Runtime (approx.): $(($diff / 60)) min(s) $(($diff % 60)) secs"
elif [ $diff -lt 86400 ]; then
    hours=$(($diff / 3600))
    minutes=$((($diff % 3600) / 60))
    seconds=$(($diff % 60))
    echo "Runtime (approx.): $hours hour(s) $minutes min(s) $seconds secs"
else
    days=$(($diff / 86400))
    hours=$((($diff % 86400) / 3600))
    minutes=$((($diff % 3600) / 60))
    seconds=$(($diff % 60))
    echo "Runtime (approx.): $days day(s) $hours hour(s) $minutes min(s) $seconds secs"
fi
