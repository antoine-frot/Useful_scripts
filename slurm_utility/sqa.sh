#!/bin/bash
# Displays SLURM job ID, names, time, CPUs and memory which fit the terminal width.
# Also display the number of jobs runnig

job_id_width=$(squeue -u $USER -o "%i" | awk '{print length($0)}' | sort -nr | head -n 1)
time_width=$(squeue -u $USER -o "%M" | awk '{print length($0)}' | sort -nr | head -n 1)
cpu_count_width=$(squeue -u $USER -o "%C" | awk '{print length($0)}' | sort -nr | head -n 1)
memory_usage_width=$(squeue -u $USER -o "%m" | awk '{print length($0)}' | sort -nr | head -n 1)
name_width=$(squeue -u $USER -o "%j" | awk '{print length($0)}' | sort -nr | head -n 1)

job_id_width=$((job_id_width < 5 ? 5 : job_id_width))
time_width=$((time_width < 4 ? 4 : time_width))
cpu_count_width=$((cpu_count_width < 4 ? 4 : cpu_count_width))
memory_usage_width=$((memory_usage_width < 8 ? 8 : memory_usage_width))
name_width=$((name_width < 4 ? 4 : name_width))

terminal_width=$(tput cols)
maximal_name_width=$((terminal_width - job_id_width - time_width - cpu_count_width - memory_usage_width - 4)) # -4 beacause of the spaces
if [ $maximal_name_width -lt 4 ]; then
    echo "Terminal too narrow."
    exit 1
elif [ $name_width -gt $maximal_name_width ]; then
    name_width=$maximal_name_width
fi

squeue -u $USER -o "%.${job_id_width}i %.${name_width}j %.${time_width}M %.${cpu_count_width}C %.${memory_usage_width}m"
echo "Number of jobs running: $(($(squeue --me --noheader | wc -l)))"
