#!/bin/bash
# Displays SLURM job ID, names, time, CPUs and memory which fit the terminal width.
# Also display the number of jobs running

# Get all job information in a single squeue call and store it
job_data=$(squeue -u $USER -o "%i %j %M %C %m" --noheader)
job_count=$(echo "$job_data" | wc -l)

# Only name and time are adapted but the script is faser
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
    maximal_name_width=$((terminal_width - time_width - 4 - 35)) # -4 for spaces and -19 for the other informations

    if [ $maximal_name_width -lt 4 ]; then
        echo "Terminal too narrow."
        exit 1
    elif [ $name_width -gt $maximal_name_width ]; then
        name_width=$maximal_name_width
    fi
    
    # Finally display
    squeue -u $USER -o "%.8i %.${name_width}j %.${time_width}M %.4C %.7m %R"
fi

echo "Number of jobs running: $job_count"


exit 0
# Everything is adopted but slower
if [ "$job_count" -gt 0 ]; then
    # Calculate column widths
    while read -r line; do
        id=$(echo "$line" | awk '{print $1}')
        name=$(echo "$line" | awk '{print $2}')
        time=$(echo "$line" | awk '{print $3}')
        cpu=$(echo "$line" | awk '{print $4}')
        mem=$(echo "$line" | awk '{print $5}')
        
        id_len=${#id}
        name_len=${#name}
        time_len=${#time}
        cpu_len=${#cpu}
        mem_len=${#mem}
        
        [ "$id_len" -gt "${job_id_width:-0}" ] && job_id_width=$id_len
        [ "$name_len" -gt "${name_width:-0}" ] && name_width=$name_len
        [ "$time_len" -gt "${time_width:-0}" ] && time_width=$time_len
        [ "$cpu_len" -gt "${cpu_count_width:-0}" ] && cpu_count_width=$cpu_len
        [ "$mem_len" -gt "${memory_usage_width:-0}" ] && memory_usage_width=$mem_len
    done <<< "$job_data"
    
    # Apply minimum width constraints
    job_id_width=$((job_id_width < 5 ? 5 : job_id_width))
    time_width=$((time_width < 4 ? 4 : time_width))
    cpu_count_width=$((cpu_count_width < 4 ? 4 : cpu_count_width))
    memory_usage_width=$((memory_usage_width < 7 ? 7 : memory_usage_width))
    name_width=$((name_width < 4 ? 4 : name_width))
    
    # Calculate terminal width constraints
    terminal_width=$(tput cols)
    maximal_name_width=$((terminal_width - job_id_width - time_width - cpu_count_width - memory_usage_width - 4))
    
    if [ $maximal_name_width -lt 4 ]; then
        echo "Terminal too narrow."
        exit 1
    elif [ $name_width -gt $maximal_name_width ]; then
        name_width=$maximal_name_width
    fi

    # Finally display
    squeue -u $USER -o "%.${job_id_width}i %.${name_width}j %.${time_width}M %.${cpu_count_width}C %.${memory_usage_width}m"
fi

echo "Number of jobs running: $job_count"
