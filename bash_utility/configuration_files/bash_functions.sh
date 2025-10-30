#!/bin/bash
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

get_main_dir () {
	# Get the closest directory containing MAIN_DIR
	local current_dir=$(pwd)
	local main_dir=""
	local temp_dir="$current_dir"
	while [ "$temp_dir" != "/" ]; do
	    if [ -f "$temp_dir/MAIN_DIR" ]; then
		main_dir="$temp_dir"
		break
	    fi
	    temp_dir=$(dirname "$temp_dir")
	done

	if [ -z "$main_dir" ]; then
	    echo "Error: MAIN_DIR not found in any parent directory. Go not go back to previous main directory" >&2
        return 1
	else
	    echo $main_dir
        return 0
	fi
}

goto() {
    if [[ $# -ne 1 || "$1" != *"-"* ]]; then
        echo "Usage: goto molecule-method" >&2
        return 1
    fi
    
    local target_dir=$(echo "$1" | sed 's/-/\//g')
    local main_dir=$(get_main_dir) || exit 1
    local full_path="$main_dir/$target_dir"
    
    if [[ -d "$full_path" ]]; then
        cd "$full_path"
    else
        echo "Error: Directory '$full_path' does not exist" >&2
        return 1
    fi
}

back_to_main() {
    local main_dir=$(get_main_dir) || exit 1
    cd $main_dir
}
