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

back_to_main() {
	# Change direcoty to the closest directory containing MAIN_DIR
	current_dir=$(pwd)
	main_dir=""
	temp_dir="$current_dir"
	while [ "$temp_dir" != "/" ]; do
	    if [ -f "$temp_dir/MAIN_DIR" ]; then
		main_dir="$temp_dir"
		break
	    fi
	    temp_dir=$(dirname "$temp_dir")
	done

	if [ -z "$main_dir" ]; then
	    echo "Error: MAIN_DIR not found in any parent directory. Go not go back to previous main directory" >&2
	else
	    cd $main_dir
	fi
}
