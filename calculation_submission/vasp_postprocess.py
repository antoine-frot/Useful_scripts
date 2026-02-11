#!/home/afrot/Useful_scripts/.venv/bin/python3
"""
Post-processing script for VASP calculations.
Runs independently after job submission.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: vasp_postprocess.py <job_name> <vasp_job_id>")
        sys.exit(1)
    
    job_name = sys.argv[1]
    vasp_job_id = sys.argv[2]
    
    wait_and_postprocess(job_name, vasp_job_id)
