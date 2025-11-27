find . -type l -print0 | while IFS= read -r -d '' linkname; do
    target=$(readlink "$linkname")
    
    if [[ "$target" == *"../workflow_tools/orca/"* ]]; then
        dir=$(dirname "$linkname")
        filename=$(basename "$linkname")
        
        # Perform the rename
        mv "$linkname" "${dir}/orca_${filename}"
        echo "Renamed $linkname -> ${dir}/orca_${filename}"
    fi
done
