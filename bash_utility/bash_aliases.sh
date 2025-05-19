#############
# Functions #
#############

# copy in the clipboard for facilitating exportation
copy() { cat $1 | xclip -sel clip
}

#############
# Variables #
#############

psmn="afrot@allo-psmn.psmn.ens-lyon.fr"
lake="${USER}@cl6226comp2.psmn.ens-lyon.fr"
cascade="${USER}@s92node01.psmn.ens-lyon.fr"

script="~/script"
slurm_utility="$script/slurm_utility"
bash_utility="$script/bash_utility"
workflow_tools="$script/workflow_tools/orca"

###########
# Aliases #
###########

alias cputime="sreport -t Hour cluster AccountUtilizationByUser Start=2025-01-01 Users=$USER"
alias sq='squeue -u $USER -o "%.76j %.10M"; echo "Number of jobs running: $(($(squeue --me --noheader | wc -l)))"'
alias sqa='squeue -u $USER -o "%.8i %.120j %.10M %.4C %.8m"; echo "Number of jobs running: $(($(squeue --me --noheader | wc -l)))"'
alias ls='ls --color'

alias scancelall="$slurm_utility/scancelall.sh"
alias scancelname="python3 $slurm_utility/scancelname.py"

alias get_geom="$workflow_tools/get_geom.sh"
alias get_transition="python3 $workflow_tools/get_transition.py"
alias get_error="$workflow_tools/get_error.sh"
alias get_chiroptic="python3 $workflow_tools/get_chiroptic.py"
alias get_difference_densities="python3 $workflow_tools/get_difference_densities.py"

alias rename_dir="$bash_utility/rename_dir.sh"
alias rename_files="$bash_utility/rename_files.sh"
alias remove_pattern="python3 $bash_utility/remove_pattern.py"

alias submit_orca="$script/submit_orca.sh"
alias submit_turbomole="$script/submit_turbomole.sh"


alias molden="/home/ssteinma/bin/molden"
