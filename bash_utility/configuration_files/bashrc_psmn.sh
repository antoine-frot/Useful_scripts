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

#######################
# Variables & Aliases #
#######################

export path_orca="/Xnfs/chimie/debian11/orca/orca_6_0_1"
TURBODIR=/home/rrullan/TmoleX2024/TURBOMOLE
source $TURBODIR/Config_turbo_env
alias orca_plot="$path_orca/orca_plot"
alias molden="/home/ssteinma/bin/molden"