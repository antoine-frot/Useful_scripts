#!/bin/bash
# Displays SLURM job information which fits the terminal width.
# Also displays the number of jobs running
# Usage: script_name [username] [mode]
#   username: SLURM username (default: $USER)
#   mode: 'simple' for basic output, 'full' for detailed output (default: simple)

# Parse arguments
mode=${1:-simple}
user=${2:-$USER}

# Validate mode
if [[ "$mode" != "simple" && "$mode" != "full" ]]; then
    echo "Error: Mode must be 'simple' or 'full'"
    echo "Usage: $0 [simple|full] [username]"
    exit 1
fi

# Get all job information in a single squeue call and store it
job_data=$(squeue -u $user -o "%i %j %M %C %m" --noheader)
if [ -z "$job_data" ]; then
    echo "No jobs running."
    exit 0
fi
job_count=$(echo "$job_data" | wc -l)

if [ "$job_count" -gt 0 ]; then
    # Calculate column widths for name and time
    name_width=0
    time_width=0
    
    while read -r line; do
        name=$(echo "$line" | awk '{print $2}')
        time=$(echo "$line" | awk '{print $3}')

        name_len=${#name}
        time_len=${#time}

        [ "$name_len" -gt "$name_width" ] && name_width=$name_len
        [ "$time_len" -gt "$time_width" ] && time_width=$time_len
    done <<< "$job_data"

    # Apply minimum width constraints
    time_width=$((time_width < 4 ? 4 : time_width))

    # Calculate terminal width constraints based on mode
    terminal_width=$(tput cols)
    
    if [ "$mode" = "simple" ]; then
        # Simple mode: only name and time
        maximal_name_width=$((terminal_width - time_width - 1)) # -1 for space between columns
        output_format="%.${name_width}j %.${time_width}M"
    else
        # Full mode: ID, name, time, CPUs, memory, priority, reason
        maximal_name_width=$((terminal_width - time_width - 6 - 43)) # -6 for spaces, -43 for other info
        output_format="%.8i %.${name_width}j %.${time_width}M %.4C %.7m %.8Q %R"
    fi

    # Check if terminal is wide enough
    if [ $maximal_name_width -lt 4 ]; then
        echo "Terminal too narrow."
        exit 1
    elif [ $name_width -gt $maximal_name_width ]; then
        name_width=$maximal_name_width
        # Update the format string with the adjusted name width
        if [ "$mode" = "simple" ]; then
            output_format="%.${name_width}j %.${time_width}M"
        else
            output_format="%.8i %.${name_width}j %.${time_width}M %.4C %.7m %.8Q %R"
        fi
    fi
    
    # Display the jobs
    squeue -u $user -o "$output_format"
fi

echo "Number of jobs running: $job_count"
