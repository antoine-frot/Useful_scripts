#############
# Variables #
#############

if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:$path_to_git/bin:" ]]
then
    PATH="$HOME/.local/bin:$HOME/bin:$path_to_git/bin:$PATH"
fi
export PATH

export PYTHONPATH="$path_to_git:$PYTHONPATH"
export EDITOR=vim # the default EDITOR is set to vim
Submitted="$HOME/Submitted.txt"
python_env () {
    if [ -n $VIRTUAL_ENV ]; then
        echo "[${VIRTUAL_ENV##*/}]"
    else
        echo''
    fi
}
if [ -f ~/.git-prompt.sh ]; then
  source ~/.git-prompt.sh
fi
PS1='$(python_env)$(__git_ps1 " (%s)") \h:\w\$ '
# PS1='\u@\h:\w$(__git_ps1 " (%s)")$(python_env)$ '
