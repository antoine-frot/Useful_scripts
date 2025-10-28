mesg y
export PYTHONPATH="$path_to_git:$PYTHONPATH"
export EDITOR=vim # the default EDITOR is set to vim
# Source global definitions
# if [ -f /etc/bashrc ]; then
#  	. /etc/bashrc
# fi
if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]
then
    PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi
export PATH
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
