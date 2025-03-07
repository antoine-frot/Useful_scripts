#!/bin/bash
#SBATCH -J SS
##SBATCH -p Cascade
#SBATCH -p Cascade
#SBATCH -o %j.out
#SBATCH -e %j.err
#SBATCH --nodes=1
#SBATCH -n 16
##SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --mem=100000               # Min memory requested per node (MB) 
#SBATCH --time=7-23:00:00
#


start=$(date +%s)
echo "START_TIME           = `date +'%y-%m-%d %H:%M:%S'`"

diractual=$(pwd)

# Create a scratchdir at the local node
SCRATCHDIR=`mktemp -d`
HOMEDIR="$SLURM_SUBMIT_DIR"

cd ${HOMEDIR} || { echo "cannot cd to ${HOMEDIR}"; exit 1; }
cp auxbasis coord control mos basis  "${SCRATCHDIR}"
cd  "${SCRATCHDIR}" || { echo "cannot cd to ${SCRATCHDIR}"; exit 1; }

# set Parallel
export OMP_NUM_THREADS=$SLURM_NTASKS_PER_NODE
export PARA_ARCH=SMP
#export PARA_ARCH=OMP        #para rodar o NumForce
export PARNODES=$SLURM_NTASKS
#export PARNODES=$SLURM_CPUS_ON_NODE
export TM_PAR_FORK=yes
#ulimit -s unlimited

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
echo "NODE: $(uname -n)"
echo "PARA_ARCH: " $PARA_ARCH
echo "SYSNAME:  " $(sysname)

export TURBODIR='/home/jtoldo/softs/TmoleX2024/TURBOMOLE'
export TURBOMOLE_SYSNAME=em64t-unknown-linux-gnu_smp
export PATH=$PATH:$TURBODIR/scripts
export PATH=$PATH:$TURBODIR/bin/`sysname`
source ${TURBODIR}/Config_turbo_env

echo "TURBODIR: " $TURBODIR
echo "================================="
echo ""

# Initialize TURBOMOLE completion flag
TURBOMOLE_calc_done=0
TURBOMOLE_isdone="${SCRATCHDIR}/${SLURM_JOB_ID}.isdone"
echo "$TURBOMOLE_calc_done" > "$TURBOMOLE_isdone"

#********************************************************************
#                      TURBOMOLE EXECUTION:
#********************************************************************
# TURBOTEST  (installation test):
# TTEST    # from TURBOMOLE/TURBODIR/TURBOTEST
#
#                          SINGLE POINT
#********************************************************************
#***************************** SCF **********************************
# dscf >> dscf.out
# ridft >> ridft.out
#***************************** RICC2/ADC2****************************
 #dscf > dscf.out
( ridft > ridft.out; ricc2 > ricc2.out; TURBOMOLE_calc_done=1; echo "$TURBOMOLE_calc_done" > "$TURBOMOLE_isdone"; echo "all done") &
#***************************** TDDFT ********************************
# nohup  dscf  > dscf.out
# escf  > escf.out
#***************************** RI-TDDFT ********************************
# ridft  > ridft.out
# escf  > escf.out
#********************************************************************
#
#                     GEOMETRY OPTIMIZATION
#********************************************************************
######coordinates:
# t2x (all geom)
# t2x coord > coord.initial.xyz
# t2x -c 
#************************** SCF *************************************
# jobex -ri -level scf -gcart 4 -c 500 > jobex.out
# jobex -ri -gcart 4 -c 100 > jobex.out
#************************* RICC2/ADC(2) ************************************
#  jobex -level cc2 -c 100
#  jobex -level cc2 -gcart 4 -c 500   > jobex.out  
#  GROUND STATE FOR ADC(2) ENERGIES using SCS-MP2 (selected from ricc2 menu): RECOMMENDED:
#  jobex -ri -level cc2 -energy 7 -gcart 4 -c 100
#  GROUND STATE RIMP2 (selected from mp2 menu):
#  jobex -ri -level mp2 -gcart 4 -c 100
#**********************(RI) DFT Ground state ************************
# jobex -c 300 
# jobex -ri -dscf 
#********************* TDDFT Excited state **************************
# jobex -ex -c 300 
# jobex -ri -ex -gcart 4 -c 500 > jobex.out
#********************* Transition state OPT *************************
# DFT:
# jobex -trans -c 300 
# TDDFT:
#  jobex -ex -trans -keep -c 300
## ******************************************************************
#
#                          GRADIENTS
#******************************************************************
#                        Ground state DFT
# dscf  > scf.out
# rdgrad > rdgrad.out
#*******************************************************************
#                       Excited state TDDFT
# dscf  > scf.out
# egrad > grad.out
#******************************************************************
#
#                        FORCE CONSTANTS
#******************************************************************
#************************* AOForce*********************************
# SCF/DFT:
# aoforce > aoforce.out     
#************************** NumForce******************************
#                      Normal modes CC2
#### run NumForce in the same way for GS and ES
#### For single points in several nodes:
# cat /dev/null > nodefile
# for i in $(seq 1 $SLURM_CPUS_ON_NODE); do hostname  >> nodefile; done
## where nodefiles is a list of nodes
# numForce -central -level cc2 -mfile nodefile > NumForce.out

#### For parallel:
# NumForce -central -level cc2 > NumForce.out
# NumForce -level cc2 > NumForce.out
# NumForce -central -level dft > NumForce.out
#

#====================================================================

# Periodically copy output files from scratch to home directory                 
while [ "$TURBOMOLE_calc_done" -eq 0 ]                                               
do                                                                              
  sleep 60
  TURBOMOLE_calc_done=$(<"$TURBOMOLE_isdone")
  cp *.out ${HOMEDIR}/
done

# At the local node:
rm -r CC* cc2-* "$TURBOMOLE_isdone" # remove integrals
cp * ${HOMEDIR}/
rm -vrf "${SCRATCHDIR}"

# Append to Submited.txt
echo "$SLURM_JOB_NAME" >> $diractual/Submited.txt

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
