#!/bin/bash
# Displays SLURM job names and runtime which fit the terminal width.
# Also display the number of jobs runnig

# Get all job information in a single squeue call and store it
job_data=$(squeue -u $USER -o "%i %j %M %C %m" --noheader)
job_count=$(echo "$job_data" | wc -l)

if [ "$job_count" -gt 0 ]; then
    # Calculate column widths
    while read -r line; do
        name=$(echo "$line" | awk '{print $2}')
        time=$(echo "$line" | awk '{print $3}')

        name_len=${#name}
        time_len=${#time}

        [ "$name_len" -gt "${name_width:-0}" ] && name_width=$name_len
        [ "$time_len" -gt "${time_width:-0}" ] && time_width=$time_len
    done <<< "$job_data"

    # Apply minimum width constraints
    time_width=$((time_width < 4 ? 4 : time_width))
    cpu_count_width=$((cpu_count_width < 4 ? 4 : cpu_count_width))

    # Calculate terminal width constraints
    terminal_width=$(tput cols)
    maximal_name_width=$((terminal_width - time_width - 1)) #-1 for the space between the columns

    if [ $maximal_name_width -lt 4 ]; then
        echo "Terminal too narrow."
        exit 1
    elif [ $name_width -gt $maximal_name_width ]; then
        name_width=$maximal_name_width
    fi
    
    # Finally display
    squeue -u $USER -o "%.${name_width}j %.${time_width}M"
fi

echo "Number of jobs running: $job_count"
