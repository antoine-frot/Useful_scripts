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

#############
# Variables #
#############

psmn="afrot@allo-psmn.psmn.ens-lyon.fr"
lake="${USER}@cl6226comp2.psmn.ens-lyon.fr"
cascade="${USER}@s92node01.psmn.ens-lyon.fr"

###########
# Aliases #
###########

# general aliases
alias cputime="sreport -t Hour cluster AccountUtilizationByUser Start=2025-01-01 Users=$USER"
alias terrorisme="sreport -t Hour cluster AccountUtilizationByUser Start=2025-01-01 Users=$USER"
alias ls='ls --color'

# Aliases for scripts in the git repository
alias get_chiroptic="python3 $path_to_git/data_visualisation/get_chiroptic.py"

# Generate aliases for all usefull scripts in workflow
OUTPUT_GENERATE_ALIASE="$HOME/.generated_aliases.txt"
DIRS_WITH_SCRIPTS_FOR_WORKFLOW=("bash_utility" "calculation_submission" "get_properties/orca" "slurm_utility" "workflow_tools" "workflow_tools/orca" "workflow_tools/geometry_tools" "workflow_tools/fcclasses3")

if [ -f "$OUTPUT_GENERATE_ALIASE" ]; then
    rm "$OUTPUT_GENERATE_ALIASE"
fi

for dir in "${DIRS_WITH_SCRIPTS_FOR_WORKFLOW[@]}"; do
    echo "# $dir" >> "$OUTPUT_GENERATE_ALIASE"
    bash "$path_to_git/bash_utility/configuration_files/generate_aliases.sh" "$path_to_git/$dir" >> "$OUTPUT_GENERATE_ALIASE"
done

source "$OUTPUT_GENERATE_ALIASE"
