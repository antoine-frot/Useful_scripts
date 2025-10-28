#!/bin/bash
###########
# Aliases #
###########

# general aliases
alias cputime="sreport -t Hour cluster AccountUtilizationByUser Start=2025-01-01 Users=$USER"
alias terrorisme="sreport -t Hour cluster AccountUtilizationByUser Start=2025-01-01 Users=$USER"
alias ls='ls --color'
alias glog='git log --all --decorate --oneline --graph'
alias Submitted='vim ~/Submitted.txt'

# Aliases for scripts in the git repository
alias get_chiroptic="python3 $path_to_git/data_visualisation/get_chiroptic.py"

# Generate aliases for all usefull scripts in workflow
#OUTPUT_GENERATE_ALIASE="$HOME/.generated_aliases.txt"
#DIRS_WITH_SCRIPTS_FOR_WORKFLOW=("bash_utility" "calculation_submission" "get_properties/orca" "slurm_utility" "workflow_tools" "workflow_tools/orca" "workflow_tools/geometry_tools" "workflow_tools/fcclasses3" "workflow_tools/vasp")
#if [ -f "$OUTPUT_GENERATE_ALIASE" ]; then
#    rm "$OUTPUT_GENERATE_ALIASE"
#fi
#for dir in "${DIRS_WITH_SCRIPTS_FOR_WORKFLOW[@]}"; do
#    echo "# $dir" >> "$OUTPUT_GENERATE_ALIASE"
#    bash "$configuration_files/generate_aliases.sh" "$path_to_git/$dir" >> "$OUTPUT_GENERATE_ALIASE"
#done
#source "$OUTPUT_GENERATE_ALIASE"
