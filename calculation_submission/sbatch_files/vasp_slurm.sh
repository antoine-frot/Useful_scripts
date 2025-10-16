#!/bin/bash
# Project:
##SBATCH --account=YourProject
# Wall clock limit:
#SBATCH --time=2400:00:00
#SBATCH -N 1
#SBATCH --partition=main

start=$(date +%s)
echo -e "START_TIME           = `date +'%y-%m-%d %H:%M:%S'`"

echo ""
echo "===== SLURM JOB INFORMATION ====="
echo "Job ID: $SLURM_JOB_ID"
echo "Job Name: $SLURM_JOB_NAME"
echo "Node List: $SLURM_JOB_NODELIST"
echo "Number of Nodes: $SLURM_JOB_NUM_NODES"
#echo "Number of Tasks: $SLURM_NTASKS"
#echo "Number of CPUs per Task: $SLURM_CPUS_PER_TASK"
#echo "Memory Requested per Node: $SLURM_MEM_PER_NODE"
#echo "Memory Requested per CPU: $SLURM_MEM_PER_CPU"
echo "Partition: $SLURM_JOB_PARTITION"
echo "Submit Directory: $SLURM_SUBMIT_DIR"
echo "Submit Host: $SLURM_SUBMIT_HOST"
echo "Vasp version: $vasp_version"
#echo "Allocated GPUs: $SLURM_GPUS"
echo "================================="
echo ""

# From icgm file
ulimit -s unlimited
source /usr/local/bin/envgf-impi.sh
export I_MPI_PIN=on
export UCX_RC_MLX5_TX_NUM_GET_BYTES=256k
export UCX_RC_MLX5_MAX_GET_ZCOPY=32k

echo " "
echo "### Calling VASP command ..."
echo " "
mpirun -bootstrap slurm /home/sol/Vasp/$vasp_version/bin/vasp_std &
vasp_pid=$!

# Loop during the calculation
submitted_file="$HOME/Submitted.txt"
advice_pattern="> ADVICE to this user running VASP <"
warning_pattern="W    W   A  A   R    R  NN   N  II  NN   N  G    G  !!!"
advice_found=0
warning_found=0

waiting_time=1
loop_counter=0
while kill -0 "$vasp_pid" 2>/dev/null; do
  sleep $waiting_time
  if [ "$advice_found" -eq 0 ] && grep -qF "$advice_pattern" OUTCAR; then
    echo "ADVICE: $SLURM_JOB_NAME" >> $submitted_file
    advice_found=1
  fi
  if [ "$warning_found" -eq 0 ] && grep -qF "$warning_pattern" OUTCAR; then
    echo "WARNING: $SLURM_JOB_NAME" >> $submitted_file
    warning_found=1
  fi
  if [ $loop_counter -eq 180 ]; then
	  waiting_time=10
  else
	  (( loop_counter++ ))
  fi
done

# Check the exit statue of VASP
wait "$vasp_pid"
vasp_exit_code=$?
echo "VASP exit code: $vasp_exit_code"

# Check if the calculation terminated normally and write it in the ouput and Submited file
hurray_pattern="General timing and accounting informations for this job:"
if grep -iq "$hurray_pattern" OUTCAR; then
    echo "HURRAY: $SLURM_JOB_NAME" >> $submitted_file
    echo "Calculation terminated normally."
else
    echo "ERROR: $SLURM_JOB_NAME" >> $submitted_file
    echo "Calculation terminated ABnormally."
fi

# Get time of the calculation
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
