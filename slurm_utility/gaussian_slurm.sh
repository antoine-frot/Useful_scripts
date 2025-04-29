#!/bin/bash
#SBATCH -J amidine
#SBATCH -p Lake,E5,Cascade
#SBATCH -o %j.out
#SBATCH -e %j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=200G
#SBATCH --cpus-per-task=32
#SBATCH --time=192:00:00
#
module purge
##module use /applis/PSMN/debian11/E5/modules/all
module use /applis/PSMN/debian11/Lake/modules/all/
module use /home/tjiang/modules/lmod/debian11
module load gaussian/g16-avx

source $g16root/g16/bsd/g16.profile
export Gaussian=$g16root/g16/g16

job=formeA_Opc_scap
ExtIn=com
ExtOut=log

#/scratch/Chimie for Lake partition
#/scratch/E5N for E5 partition

if [[ -d "/scratch/Chimie" ]]
then
    SCRATCHDIR="/scratch/Chimie/${USER}/${SLURM_JOB_ID}/"
elif [[ -d "/scratch/E5N" ]]
then
    SCRATCHDIR="/scratch/E5N/${USER}/${SLURM_JOB_ID}/"
elif [[ -d "/scratch/Cascade" ]]
then
    SCRATCHDIR="/scratch/Cascade/${USER}/${SLURM_JOB_ID}/"
else
    echo "/scratch not found, cannot create ${SCRATCHDIR}"
    exit 1
fi

mkdir -p ${SCRATCHDIR}

CalcDir=${SCRATCHDIR}
export GAUSS_SCRDIR=${CalcDir}
HOMEDIR="$SLURM_SUBMIT_DIR"

NChk=` grep -i "chk" ${job}.${ExtIn} | head -1 | sed 's/=/ /g' | awk '{print $2}'`
if [ "$NChk" != "" ]
then
NChk=` basename $NChk .chk`.chk
fi
if [[ -s ${HOMEDIR}/${NChk} ]]
then
    cp ${HOMEDIR}/${NChk} ${CalcDir}/${NChk}
fi
if [[ -s ${HOMEDIR}/${NChk}.gz ]]
then
    cp ${HOMEDIR}/${NChk}.gz ${CalcDir}/${NChk}.gz
    gunzip ${CalcDir}/${NChk}.gz
fi

cp ${HOMEDIR}/${job}.${ExtIn} ${CalcDir}/

if [[ -s ${HOMEDIR}/${job}.${ExtOut} ]]
then
    Ext=1
    while [[ -s ${HOMEDIR}/${job}.${ExtOut}_${Ext} ]]
    do
        let Ext=Ext+1
    done
    mv ${HOMEDIR}/${job}.${ExtOut} ${HOMEDIR}/${job}.${ExtOut}_${Ext}
fi

cd ${CalcDir}
ls -al
${Gaussian} < ${job}.${ExtIn} > ${HOMEDIR}/${job}.${ExtOut}

cp * ${HOMEDIR}/



