#!/bin/bash
# Project:
##SBATCH --account=YourProject
# Wall clock limit:
#SBATCH --time=2400:00:00
#SBATCH -N 1
#SBATCH --partition=main

# Get vasp_path from first argument
vasp_path="$1"

if [ -z "$vasp_path" ]; then
    echo "Error: VASP path not provided as argument"
    exit 1
fi
vasp_bin=$vasp_path/bin/vasp_std
if [ ! -x "$vasp_bin" ]; then
    echo "Error: VASP executable not found or not executable at $vasp_bin"
    exit 1
fi

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
echo "Vasp path: $vasp_path"
#echo "Allocated GPUs: $SLURM_GPUS"
echo "================================="
echo ""

# Function to handle job cancellation
handle_cancel() {
    # Write CANCELLED status and remove RUNNING status
    echo "CANCELLED: $displayed_name" >> "$submitted_file"
    sed -i "/RUNNING: ${displayed_name//\//\\/}/d" "$submitted_file"
    
    # Kill the VASP process if it's running
    if kill -0 "$vasp_pid" 2>/dev/null; then
        kill -9 "$vasp_pid"
    fi
    
    exit 143 # Exit with a code indicating termination by signal
}

display_calculation_duration() {
    # Get time of the calculation
    end=$(date +%s)
    echo "END_TIME           = `date +'%y-%m-%d %H:%M:%S'`"
    echo " "
    echo "### Calculate duration ..."
    echo " "
    diff=$((end-start))
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
}
# Trap the termination signals
trap 'display_calculation_duration; handle_cancel' SIGTERM SIGINT

# From icgm file
echo "Setting up environment for $SLURM_SUBMIT_HOST..."
if [ $SLURM_SUBMIT_HOST == "taz.d5.icgm.fr" ]; then
    ulimit -s unlimited
    source /usr/local/bin/envgf-impi.sh
    export I_MPI_PIN=on
    export UCX_RC_MLX5_TX_NUM_GET_BYTES=256k
    export UCX_RC_MLX5_MAX_GET_ZCOPY=32k
elif [ $SLURM_SUBMIT_HOST == "tornado" ]; then
    source /usr/local/bin/gnu11-mkl-impi.sh                                                                                                                                                                                                     
    export I_MPI_PIN_RESPECT_HCA=1
    export I_MPI_PIN=on
    ulimit -s unlimited
else
    echo "Unknown submit host: $SLURM_SUBMIT_HOST. No specific environment setup applied."
fi


echo " "
echo "### Calling VASP command ..."
echo " "
mpirun -bootstrap slurm $vasp_bin &
vasp_pid=$!

# Loop during the calculation
submitted_file="$HOME/Submitted.txt"
#advice_pattern="> ADVICE to this user running VASP <"
advice_pattern="ADVICE"
warning_pattern="W    W   A  A   R    R  NN   N  II  NN   N  G    G  !!!"
advice_found=0
warning_found=0

waiting_time=1
loop_counter=0
displayed_name="$SLURM_JOB_NAME ($SLURM_JOB_ID)"
# Remove entry from previous job for this calculation if exists
sed -i "/ ${SLURM_JOB_NAME} /d" $submitted_file
echo "RUNNING: $displayed_name" >> $submitted_file
while kill -0 "$vasp_pid" 2>/dev/null; do
  sleep $waiting_time
  if [ "$advice_found" -eq 0 ] && grep -qF "$advice_pattern" OUTCAR 2>/dev/null; then
    echo "ADVICE: $displayed_name" >> $submitted_file
    advice_found=1
  fi
  if [ "$warning_found" -eq 0 ] && grep -qF "$warning_pattern" OUTCAR 2>/dev/null; then
    echo "WARNING: $displayed_name" >> $submitted_file
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
    echo "HURRAY: $displayed_name" >> "$submitted_file"
    echo "Calculation terminated normally."
else
    echo "ERROR: $displayed_name" >> "$submitted_file"
    echo "Calculation terminated ABnormally."
fi
sed -i "/RUNNING: ${displayed_name//\//\\/}/d" "$submitted_file"
display_calculation_duration