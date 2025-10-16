#!/usr/bin/env python3
"""
scancelname.py - Cancel Slurm jobs by name pattern with confirmation.

This script allows users to cancel Slurm jobs by specifying job name patterns,
including support for Unix-style wildcards (*, ?, [seq]). It lists matching jobs,
prompts for confirmation, and cancels only if explicitly approved.

Usage:
    ./scancelname.py <job_name_pattern> [<pattern2> ...]

Examples:
    ./scancelname.py "myjob*"            # Cancel jobs with names starting with 'myjob'
    ./scancelname.py "preprocess*" "train_?"  # Cancel jobs matching multiple patterns

Features:
    - Supports wildcards in job names
    - Lists jobs to be cancelled before prompting
    - Requires explicit confirmation (defaults to 'No')
    - Only cancels jobs owned by the current user
"""

import sys
import subprocess
import fnmatch
import os
import argparse

def get_current_user():
    """Get current username"""
    try:
        return os.getenv('USER') or os.getenv('LOGNAME')
    except Exception as e:
        print(f"Error getting username: {e}")
        sys.exit(1)

def get_jobs(user):
    """Get list of jobs for current user using squeue"""
    try:
        result = subprocess.run(
            ['squeue', '--user', user, '--format=%i %j', '--noheader'],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.strip().split(maxsplit=1) for line in result.stdout.splitlines()]
    except subprocess.CalledProcessError as e:
        print(f"Error getting jobs: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

def cancel_jobs(patterns):
    """Cancel jobs matching name patterns with confirmation"""
    user = get_current_user()
    jobs = get_jobs(user)
    
    matches = []
    for job_id, job_name in jobs:
        for pattern in patterns:
            if fnmatch.fnmatchcase(job_name, pattern):
                matches.append((job_id, job_name))
    
    if not matches:
        print(f"No matching jobs found for {patterns}.")
        return

    # Show jobs to be cancelled
    print("\nJobs to be cancelled:")
    for job_id, job_name in matches:
        print(f"  {job_id}: {job_name}")
    
    # Get confirmation
    response = input(f"\nAre you sure you want to cancel {len(matches)} jobs? [y/N] ").strip().lower()
    if response != 'y':
        print("Cancellation aborted.")
        return
    
    # Proceed with cancellation
    job_ids = [job[0] for job in matches]
    try:
        subprocess.run(
            ['scancel'] + job_ids,
            check=True
        )
        print(f"\nSuccessfully cancelled {len(job_ids)} jobs.")
    except subprocess.CalledProcessError as e:
        print(f"\nError cancelling jobs: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cancel Slurm jobs by name pattern with confirmation.",
        epilog="""
Examples:
  %(prog)s "myjob*"                    Cancel jobs with names starting with 'myjob'
  %(prog)s "preprocess*" "train_?"     Cancel jobs matching multiple patterns
  %(prog)s                             Cancel job running in the current working directory

Features:
  - Supports Unix-style wildcards (*, ?, [seq]) in job names
  - Lists jobs to be cancelled before prompting for confirmation
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'patterns',
        nargs='*',
        help='Job name patterns to match (supports wildcards). If no patterns provided, uses default job name from environment.'
    )
    
    args = parser.parse_args()
    
    if not args.patterns:
        path_to_git = os.getenv("path_to_git")
        if not path_to_git:
            print("Error: The environment variable 'path_to_git' is not set.")
            sys.exit(1)
        cmd = f"source {path_to_git}/calculation_submission/get_job_name.sh; get_job_name"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash")
        if result.returncode != 0:
            print(f"Error running get_job_name: {result.stderr.strip()}")
            sys.exit(1)
        cancel_jobs([result.stdout.strip()])
    else:
        cancel_jobs(args.patterns)
