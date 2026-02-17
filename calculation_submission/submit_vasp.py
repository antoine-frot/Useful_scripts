#!/usr/bin/env python3
"""
Submit VASP calculations to SLURM scheduler.
Handles version selection, partition selection, and post-processing.
"""

import os
import sys
import subprocess
import time
import re
import argparse
from pathlib import Path

def get_job_name():
    """
    Generate a job name based on the path from home directory to current directory.
    Replaces path separators with hyphens and validates that no hyphens exist
    in directory names to avoid job name conflicts.
    """
    current_dir = Path.cwd()
    home_dir = Path.home()
    
    try:
        relative_path = current_dir.relative_to(home_dir)
    except ValueError:
        print(f"Error: Current directory is not under home directory", file=sys.stderr)
        sys.exit(1)
    
    # Check if any directory name contains a hyphen
    if '-' in current_dir.name:
        print(f"Error: The directory '{current_dir.name}' contains a hyphen (-).", file=sys.stderr)
        sys.exit(1)
    
    # Replace slashes with hyphens
    job_name = str(relative_path).replace(os.sep, '-')
    
    return job_name

def get_vasp_version():
    """Get VASP version from file or user input."""
    vasp_version_file = 'VASP_version.txt'
    
    if os.path.exists(vasp_version_file):
        with open(vasp_version_file, 'r') as f:
            vasp_version = f.read().strip()
        print(f"VASP path: {vasp_version}")
        return vasp_version
    
    print("Which VASP version?")
    path_to_vasp = '/home/sol/Vasp'
    available_versions_Vasp6 = os.listdir(f'{path_to_vasp}/Vasp6')
    available_versions_Vasp6 = [v for v in available_versions_Vasp6 
                                if not v.endswith('.gz') and 
                                not v.endswith('.zip') and 
                                not v.endswith('.tgz') and 
                                not v.endswith('.tar')]
    available_versions_Vasp5 = os.listdir(f'{path_to_vasp}/Vasp5')
    available_versions_Vasp5 = [v for v in available_versions_Vasp5 
                                if not v.endswith('.gz') and 
                                not v.endswith('.zip') and 
                                not v.endswith('.tgz') and 
                                not v.endswith('.tar')]

    print("\nVASP 6 versions:")
    for i, version in enumerate(available_versions_Vasp6, 1):
        print(f"{i}) {version}")

    print("\nVASP 5 versions:")
    for i, version in enumerate(available_versions_Vasp5, len(available_versions_Vasp6) + 1):
        print(f"{i}) {version}")
    print()

    while True:
        try:
            choice = int(input(f"Enter choice (1-{len(available_versions_Vasp6) + len(available_versions_Vasp5)}): "))
            if 1 <= choice <= len(available_versions_Vasp6):
                vasp_version = f"Vasp6/{available_versions_Vasp6[choice - 1]}"
                break
            elif len(available_versions_Vasp6) < choice <= len(available_versions_Vasp6) + len(available_versions_Vasp5):
                vasp_version = f"Vasp5/{available_versions_Vasp5[choice - len(available_versions_Vasp6) - 1]}"
                break
            else:
                print("Invalid choice. Try again.")
        except (ValueError, KeyboardInterrupt):
            print("\nInvalid input. Try again.")
    
    vasp_version_path = f"{path_to_vasp}/{vasp_version}"
    with open(vasp_version_file, 'w') as f:
        f.write(vasp_version_path)

    return vasp_version_path

def get_slurm_availability():
    """Get available nodes per partition and return partition list."""
    try:
        # %P = partition, %a = availability, %F = nodes (allocated/idle/other/total)
        result = subprocess.run(['sinfo', '-h', '-o', '%P %a %F'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        available_partitions = {}
        for line in result.stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                partition = parts[0].rstrip('*')  # Remove * from default partition
                availability = parts[1]
                node_counts = parts[2].split('/')
                
                # Skip unavailable partitions
                if availability != 'up':
                    continue
                
                if len(node_counts) >= 4:
                    # node_counts = [Allocated, Idle, Other, Total]
                    idle_nodes = int(node_counts[1])
                    # Aggregate if partition appears multiple times
                    if partition in available_partitions:
                        available_partitions[partition] += idle_nodes
                    else:
                        available_partitions[partition] = idle_nodes

        if not available_partitions:
            print("No available partitions found.")
            sys.exit(1)

        return available_partitions

    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not get SLURM availability: {e}")
        sys.exit(1)

def get_partition():
    """Get partition with available node count from user input."""
    available_partitions = get_slurm_availability()

    print("Which partition? [Index) partition_name (available_nodes)]")

    partition_list = list(available_partitions.keys())
    for i, partition in enumerate(partition_list, 1):
        nodes = available_partitions[partition]
        print(f"{i}) {partition} ({nodes})")

    while True:
        try:
            choice = int(input(f"Enter choice (1-{len(available_partitions)}): "))
            if 1 <= choice <= len(available_partitions):
                return partition_list[choice - 1], available_partitions[partition_list[choice - 1]]
            else:
                print("Invalid choice. Try again.")
        except (ValueError, KeyboardInterrupt):
            print("\nInvalid input. Try again.")

def submit_vasp_job(job_name, partition, number_of_nodes, vasp_version):
    """Submit VASP job to SLURM."""
    path_to_git = os.environ.get('path_to_git')
    sbatch_script = Path(path_to_git) / 'calculation_submission' / 'sbatch_files' / 'vasp_slurm.sh'
    
    cmd = [
        'sbatch',
        f'--job-name={job_name}',
        f'--partition={partition}',
        f'--nodes={number_of_nodes}',
        str(sbatch_script),
        vasp_version  # Pass as argument to the script
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Extract job ID from output like "Submitted batch job 12345"
        match = re.search(r'(\d+)$', result.stdout.strip())
        if match:
            return match.group(1)
        else:
            print(f"Could not parse job ID from: {result.stdout}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Failed to submit VASP job: {e}")
        return None

def wait_and_postprocess(job_name, vasp_job_id):
    """Wait for job completion and run post-processing."""
    slurm_output = f"slurm-{vasp_job_id}.out"
    
    # Wait for job to finish
    while True:
        try:
            result = subprocess.run(['squeue', '-j', vasp_job_id], 
                                  capture_output=True, 
                                  text=True)
            if vasp_job_id not in result.stdout:
                break
        except subprocess.CalledProcessError:
            break
        time.sleep(60)
    
    # Check if job completed successfully
    displayed_name = f"{job_name} ({vasp_job_id})"
    submitted_file = Path.home() / 'Submitted.txt'
    
    try:
        with open(submitted_file, 'r') as f:
            content = f.read()
            if f"HURRAY: {displayed_name}" in content:
                subprocess.run(['vasp_do_bader'], check=False)
                
                if '-fukui_plus' in job_name:
                    path_to_git = os.environ.get('path_to_git')
                    chgdiff_script = Path(path_to_git) / 'workflow_tools' / 'vasp' / 'bader' / 'chgdiff.pl'
                    subprocess.run(['perl', str(chgdiff_script), '../CHGCAR', 'CHGCAR'],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    check=False)
                    if os.path.exists('CHGCAR_diff'):
                        os.rename('CHGCAR_diff', 'CHGCAR_fukui_plus')
                
                elif '-fukui_moins' in job_name:
                    path_to_git = os.environ.get('path_to_git')
                    chgdiff_script = Path(path_to_git) / 'workflow_tools' / 'vasp' / 'bader' / 'chgdiff.pl'
                    subprocess.run(['perl', str(chgdiff_script), 'CHGCAR', '../CHGCAR'],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    check=False)
                    if os.path.exists('CHGCAR_diff'):
                        os.rename('CHGCAR_diff', 'CHGCAR_fukui_moins')
    except FileNotFoundError:
        with open(slurm_output, 'a') as f:
            f.write(f"\n[Post-processing] Error: {submitted_file} file not found. Skipping post-processing.\n")
    except Exception as e:
        with open(slurm_output, 'a') as f:
            f.write(f"\n[Post-processing] Error during post-processing: {e}\n")

def main():
    """Main function."""
    # Get parameters
    job_name = get_job_name()
    partition, available_nodes = get_partition()
    while True:
        try:
            number_of_nodes = int(input(f"Number of nodes to use (available: {available_nodes}): "))
            if number_of_nodes < 1 or number_of_nodes > available_nodes:
                print(f"Invalid choice. Must be between 1 and {available_nodes}.")
                continue
            break
        except (ValueError, KeyboardInterrupt):
            print("\nInvalid input. Try again.")
    vasp_version = get_vasp_version()

    # Submit job
    vasp_job_id = submit_vasp_job(job_name, partition, number_of_nodes, vasp_version)
    
    if vasp_job_id:
        # Start post-processing in background using subprocess with nohup
        path_to_git = os.environ.get('path_to_git')
        postprocess_script = Path(path_to_git) / 'calculation_submission' / 'vasp_postprocess.py'
        
        subprocess.Popen(
            ['nohup', 'python3', str(postprocess_script), job_name, vasp_job_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print(f"Job {vasp_job_id} submitted.")
    else:
        print("Failed to submit VASP job.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit VASP job.")
    parser.add_argument("-c", "--cluster_resources", action="store_true", help="Display available cluster resources and exit.")
    args = parser.parse_args()

    if args.cluster_resources:
        available_partitions = get_slurm_availability()
        partition_list = list(available_partitions.keys())
        for i, partition in enumerate(partition_list, 1):
            nodes = available_partitions[partition]
            print(f"{i}) {partition} ({nodes})")
        sys.exit(0)

    main()
