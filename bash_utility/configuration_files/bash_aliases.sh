#############
# Functions #
#############

# copy in the clipboard for facilitating exportation
copy() { cat $1 | xclip -sel clip
}

# Perform mathematical computation
num()
{
    echo "scale=3; $*" | bc -l
}

# Copy a file or directory in multiple destinations
mcp()
{
    echo "${*:2}" | xargs -n 1 cp $1
}

#############
# Variables #
#############

psmn="afrot@allo-psmn.psmn.ens-lyon.fr"
lake="${USER}@cl6226comp2.psmn.ens-lyon.fr"
cascade="${USER}@s92node01.psmn.ens-lyon.fr"

###########
# Aliases #
###########

alias cputime="sreport -t Hour cluster AccountUtilizationByUser Start=2025-01-01 Users=$USER"
alias terrorisme="sreport -t Hour cluster AccountUtilizationByUser Start=2025-01-01 Users=$USER"
alias ls='ls --color'
