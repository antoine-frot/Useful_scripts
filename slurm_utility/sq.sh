#!/bin/bash
# Displays SLURM job names and runtime which fit the terminal width.
# Also display the number of jobs runnig

runtime_width=$(squeue -u $USER -o "%M" | awk '{print length($0)}' | sort -nr | head -n 1)
name_width=$(squeue -u $USER -o "%j" | awk '{print length($0)}' | sort -nr | head -n 1)

runtime_width=$(squeue -u $USER -o "%M" | awk '{print length($0)}' | sort -nr | head -n 1)
name_width=$(squeue -u $USER -o "%j" | awk '{print length($0)}' | sort -nr | head -n 1)

terminal_width=$(tput cols)
maximal_name_width=$((terminal_width - runtime_width - 1)) # -1 because of the space
if [ $maximal_name_width -lt 4 ]; then
    echo "Terminal too narrow."
    exit 1
elif [ $name_width -gt $maximal_name_width ]; then
    name_width=$maximal_name_width
fi

squeue -u $USER -o "%.${name_width}j %.${run_time_width}M"
echo "Number of jobs running: $(($(squeue --me --noheader | wc -l)))"
