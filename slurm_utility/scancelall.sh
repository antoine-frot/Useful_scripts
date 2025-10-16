#!/bin/bash

# Read the output of squeue into an array
mapfile -t job_ids_with_headers < <(squeue -u $USER -o "%.i")
job_ids=(${job_ids_with_headers[@]:1})

# Check if there are any jobs
if [ ${#job_ids[@]} -eq 0 ]; then
  echo "No jobs found."
  exit 0
fi

# Ask for confirmation before canceling jobs
read -n 1 -p "Are you sure you want to cancel all ${#job_ids[@]} jobs? (y/n): " confirm
echo ""
if [ "$confirm" != "y" ]; then
  echo "Job cancellation aborted."
  exit 0
fi

# Cancel the jobs
for job_id in "${job_ids[@]}"; do
  echo "Cancelling job $job_id..."
  scancel "$job_id"
done

echo "All jobs have been cancelled."

