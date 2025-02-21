#!/bin/bash

# Read the output of squeue into an array
mapfile -t job_ids < <(squeue -u $USER -o "%.i")

# Check if there are any jobs
if [ ${#job_ids[@]} -eq 1 ]; then
  echo "No jobs found."
  exit 0
fi

# Ask for confirmation before canceling jobs
read -p "Are you sure you want to cancel all jobs? (y/n): " confirm
if [ "$confirm" != "y" ]; then
  echo "Job cancellation aborted."
  exit 0
fi

# Cancel the jobs
for job_id in "${job_ids[@]:1}"; do
  echo "Cancelling job $job_id..."
  scancel "$job_id"
done

echo "All jobs have been cancelled."

