#############
# Variables #
#############

Submitted="$HOME/Submitted.txt"
source ~/.git-prompt.sh
python_env () {
    if [ -n $VIRTUAL_ENV ]; then
        echo "[${VIRTUAL_ENV##*/}]"
    else
        echo''
    fi
}
PS1='$(python_env)$(__git_ps1 " (%s)") \h:\w\$ '
# PS1='\u@\h:\w$(__git_ps1 " (%s)")$(python_env)$ '
