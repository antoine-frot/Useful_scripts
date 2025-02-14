#!/bin/bash

 
# Read the output of squeue into an array
mapfile -t job_ids < <(squeue -u $USER -o "%.i")

# Check if there are any jobs
if [ ${#job_ids[@]} -eq 1 ]; then
  echo "No jobs found."
  exit 0
fi
 
# Skip the first job ID and cancel the rest
for job_id in "${job_ids[@]:1}"; do
  echo "Cancelling job $job_id..."
  scancel "$job_id"
done

echo "All jobs have been cancelled."
