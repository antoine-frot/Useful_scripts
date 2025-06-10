#!/bin/bash
: '
Usage: goto.sh molecule-method
Go to the corresponding molecule/molecule-method directory
'
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    exec bash -c "source '$0' '$@'; exec bash"  # Auto-source the file
    exit 1
fi

if [[ "$#" -ne 1 ]]; then
    echo "Usage: source $0 molecule-method" >&2
    return 1
fi

if [[ "$1" != *"-"* ]]; then
    echo "Error: Argument must be in 'molecule-method' format." >&2
    return 1
fi

target_dir="${1%%-*}/$1"

if [[ -d "$target_dir" ]]; then
    cd "$target_dir" || { echo "Failed to enter $target_dir" >&2; return 1; }
else
    echo "Error: Directory '$target_dir' does not exist." >&2
    return 1
fi
