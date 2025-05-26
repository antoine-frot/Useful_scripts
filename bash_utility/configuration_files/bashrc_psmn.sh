# If not running interactively, don't do anything
[ -z "$PS1" ] && return
HISTCONTROL=ignoreboth
# append to the history file, don't overwrite it
shopt -s histappend
shopt -s histverify

# Disable terminal bell
set bell-style none

# Eternal bash history.
# ---------------------
# Undocumented feature which sets the size to "unlimited".
# http://stackoverflow.com/questions/9457233/unlimited-bash-history
export HISTFILESIZE=
export HISTSIZE=
export HISTTIMEFORMAT="[%F %T] "
# Change the file location because certain bash sessions truncate .bash_history file upon close.
# http://superuser.com/questions/575479/bash-history-truncated-to-500-lines-on-each-login
export HISTFILE=~/.bash_eternal_history
# Force prompt to write history after every command.
# http://superuser.com/questions/20900/bash-history-loss
PROMPT_COMMAND="history -a; $PROMPT_COMMAND"

set -b

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize
#
#############
# Functions #
#############

exp_molecules() {
    python3 -c "import sys; sys.path.append('/home/afrot/script/data_visualisation'); from experimental_data import MOLECULES_DATA; print(*[molecule['name'] for molecule in MOLECULES_DATA], sep='\n')"
}


#############
# Variables #
#############

export path_orca="/Xnfs/chimie/debian11/orca/orca_6_0_1"
TURBODIR=/home/rrullan/TmoleX2024/TURBOMOLE
source $TURBODIR/Config_turbo_env
alias orca_plot="$path_orca/orca_plot"
alias molden="/home/ssteinma/bin/molden"
 
###########
# Aliases #
###########

alias get_chiroptic="python3 /home/afrot/script/data_visualisation/get_chiroptic.py"

# Generate aliases for all usefull scripts in workflow
OUTPUT_GENERATE_ALIASE="$HOME/.generated_aliases.txt"
script="/home/afrot/script"
DIRS_WITH_SCRIPTS_FOR_WORKFLOW=("bash_utility" "calculation_submission" "get_properties/orca" "slurm_utility" "workflow_tools" "workflow_tools/orca" "workflow_tools/geometry_tools")

if [ -f "$OUTPUT_GENERATE_ALIASE" ]; then
    rm "$OUTPUT_GENERATE_ALIASE"
fi

for dir in "${DIRS_WITH_SCRIPTS_FOR_WORKFLOW[@]}"; do
    echo "# $dir" >> "$OUTPUT_GENERATE_ALIASE"
    bash "$script/bash_utility/configuration_files/generate_aliases.sh" "$script/$dir" >> "$OUTPUT_GENERATE_ALIASE"
done

source "$OUTPUT_GENERATE_ALIASE"
