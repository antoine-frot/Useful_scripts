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

exp_molecules() {
    python3 -c "import sys; sys.path.append('$path_to_git/data_visualisation'); from experimental_data import MOLECULES_DATA; print(*[molecule['name'] for molecule in MOLECULES_DATA], sep='\n')"
}

denis_molecules() {
    python3 -c "import sys; sys.path.append('$path_to_git/data_visualisation'); from experimental_data import DENIS_MOLECULES; print(*[molecule for molecule in DENIS_MOLECULES], sep='\n')"
}

goto() {
    if [[ $# -ne 1 || "$1" != *"-"* ]]; then
        echo "Usage: goto molecule-method" >&2
        return 1
    fi
    
    local molecule="${1%%-*}"
    local target_dir="$molecule/$1"
    
    if [[ -d "$target_dir" ]]; then
        cd "$target_dir"
    else
        echo "Error: Directory '$target_dir' does not exist" >&2
        return 1
    fi
}
