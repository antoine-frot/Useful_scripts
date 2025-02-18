#!/bin/bash
shopt -s nullglob

: '
Module: submit_orca_jobs.sh
Description:
    This script automates the preparation and submission of ORCA quantum chemical calculation jobs
    via SLURM. It expects exactly one input file (*.inp) and one or more geometry files (*.xyz) in
    the current directory.

    For each *.xyz file, the script will:
      - Create a dedicated directory (named after the geometry file without its extension).
      - Construct a job directory named by combining the *.xyz filename and the *.inp filename.
      - Copy and modify the input file: if the first "* xyzfile" line contains a .xyz file,
        it removes the old coordinate reference and appends the current .xyz filename.
      - Optionally insert directives to reuse previously calculated molecular orbitals if a
        corresponding *.gbw.bz2 file is found.
      - Move the geometry file into the job directory.
      - Copy a SLURM submission script and submit the job.
      - Log the job submission in a designated log file.
    Finally, the original *.inp file is moved into an "Inputs" subdirectory.
    
Usage:
    Place one *.inp file and one or more *.xyz files in the working directory, then execute:
        path/submit_orca_jobs.sh
    (The coordinates in the input file should be specified as "* xyzfile", and multiple-step jobs are supported.)
'

# --- Define Color Variables ---
NC='\033[0m'         # No Color
R='\033[0;31m'       # Red
G='\033[0;32m'       # Green
Y='\033[0;33m'       # Yellow
M='\033[0;35m'       # Magenta

# --- Set the Working Directory ---
root_dir="/home/afrot/Stage2025Tangui"
if [ "$root_dir" != "$(pwd)" ]; then
    echo -e "${R}Error: You are in the wrong directory. Please go to ${root_dir}.${NC}"
    exit 1
fi

# --- Helper Function: Prompt for Yes/No ---
prompt_yes_no() {
    # Arguments:
    #   $1: Prompt message
    # Returns true for Yes and false for No.
    local answer
    while true; do
        read -n 1 -r -p "$(echo -e "${Y}$1 (y/n)? ${NC}")" answer
        echo
        case "$answer" in
            [yY]) return 0 ;;
            [nN]) return 1 ;;
            *) echo -e "${R}Please answer y or n.${NC}" ;;
        esac
    done
}

# --- Check for Required Input Files ---

# Require exactly one *.inp file in the current directory
inp_files=( *.inp )
if (( ${#inp_files[@]} != 1 )); then
    echo -e "${R}Error: Exactly one input file (*.inp) is expected in the current directory.${NC}"
    exit 1
fi
input="${inp_files[0]}"

# Require at least one *.xyz file
xyz_files=( *.xyz )
if (( ${#xyz_files[@]} == 0 )); then
    echo -e "${R}Error: No xyz files found in the current directory.${NC}"
    exit 1
fi

# Inform the user about the number of .xyz files found
if (( ${#xyz_files[@]} == 1 )); then
    echo -e "${G}Found 1 xyz file.${NC}"
else
    echo -e "${G}Found ${M}${#xyz_files[@]}${G} xyz files.${NC}"
fi

# --- Confirm Continuation ---
if ! prompt_yes_no "Do you want to continue"; then
    echo -e "${R}Aborting.${NC}"
    exit 1
fi
echo -e "${G}Let's go!${NC}"

# --- Initialize Flags ---
two_existing_dir=1  # Indicates that at least one job directory already existed
same_parameter=1    # Flag to reuse the same parameters for existing directories
ask=0       # Flag to stop prompting the user repeatedly

# --- Process Each .xyz File ---
for xyz_file in "${xyz_files[@]}"; do
  # Create a subdirectory named after the .xyz file (without its extension)
  xyz_dir="${root_dir}/${xyz_file%.*}"
  mkdir -p "$xyz_dir"
  
  # Enter the xyz_dir directory
  pushd "$xyz_dir" > /dev/null
  
  # Construct job basename combining the .xyz filename and the input file name (both without extensions)
  job_basename="${xyz_file%.*}-${input%.*}"
  job_directory="${PWD}/${job_basename}"
  job_input="${job_basename}.inp"
  
  # If the job directory already exists, handle parameter reuse or prompt the user.
  if [ -d "$job_directory" ]; then
    if [ "$two_existing_dir" -eq 0 ] && [ "$ask" -eq 0 ]; then
      if prompt_yes_no "Do you want to keep the same parameter for all existing directories"; then
          same_parameter=0
      fi
    ask=1
    fi
    two_existing_dir=0
    echo -e "${R}Directory $(basename "$job_directory") already exists.${NC}"
    
    if (( same_parameter == 1 )); then
        if ! prompt_yes_no "Do you want to overwrite the directory"; then
            echo -e "${R}Aborting.${NC}"
            popd > /dev/null
            exit 1
        fi
    fi

    pushd "$job_directory" > /dev/null
    cp "${root_dir}/${input}" "$job_input"
    
    # --- Optionally Add Previously Calculated Molecular Orbitals ---
    if [ -f "${job_directory}.gbw" ]; then
        if (( same_parameter == 1 )); then
            use_orbs=$(prompt_yes_no "Use previously calculated molecular orbitals")
        fi

        if [ $use_orbs ]; then
            use_gbw="${job_basename}_use.gbw"
            cp "${job_directory}.gbw" "$use_gbw"
            {
                echo "!MOREAD"
                echo "%moinp ${use_gbw}"
            } > temp_insert.txt
            # Insert the molecular orbital directives after the first line of the input file.
            sed -i '2r temp_insert.txt' "$job_input"
            rm -f temp_insert.txt
            echo -e "${G}Previous calculated molecular orbitals have been used.${NC}"
        else
            echo -e "${G}Previous calculated molecular orbitals not used.${NC}"
        fi
    else
        echo -e "${G}No previous calculated molecular orbitals found.${NC}"
    fi
  else
      mkdir -p "$job_directory"
      pushd "$job_directory" > /dev/null
      cp "${root_dir}/${input}" "$job_input"
  fi 

    # --- Update the Input File with the Current .xyz File ---
    # Find the first line starting with "* xyzfile" in the input file.
    # If that line already contains a .xyz reference, remove it first.
    # Then add the .xyz file of the starting geometry.
    if xyz_line=$(grep -m1 "^\* xyzfile" "$job_input" || true); then
        if echo "$xyz_line" | grep -q "\.xyz"; then
            sed -i '/^\* xyzfile/ s/ \([^ ]*\.xyz\)$//' "$job_input"
        fi
        sed -i "0,/^\* xyzfile/ {/^\* xyzfile/ s/$/ ${xyz_file}/;}" "$job_input"
    else
        echo -e "${R}Warning: No line starting with \"* xyzfile\" was found in $job_input.${NC}"
	exit 1
    fi

    # Move the current .xyz file into the job directory
    mv "${root_dir}/${xyz_file}" "$job_directory/"
    
    # --- Prepare and Submit the Job ---
    submission_script="/home/afrot/script/orca_slurm.sh"
    if [ ! -f "$submission_script" ]; then
        echo -e "${R}Submission script not found at $submission_script.${NC}"
        popd > /dev/null
        popd > /dev/null
        exit 1
    fi
    
    # Submit the job via SLURM
    sbatch --job-name="$job_basename" "$submission_script" "$job_input" > /dev/null
    echo "$job_basename has been submitted"
    
    # Remove the temporary .gbw file if it was used
    if [ -n "${use_gbw:-}" ] && [ -f "$use_gbw" ]; then
        rm "$use_gbw"
        unset use_gbw
    fi
    
    # Log the job submission
    echo "$job_basename" >> "${root_dir}/Submited.txt"
    
    # Return to the xyz directory and then to the root directory
    popd > /dev/null  # Exit job directory
    popd > /dev/null  # Exit xyz_dir
done

# Move the original *.inp file into an "Input_Orca" directory
if prompt_yes_no "Do you want to keep the input file?"; then
  Input_directory='Input_Orca'
  mkdir -p "${root_dir}/$Input_directory"
  mv "${root_dir}/${input}" "${root_dir}/$Input_directory/${input}"
  echo "${root_dir}/${input} stored in $Input_directory."
else
  rm "${root_dir}/${input}"
fi

echo -e "${G}${#xyz_files[@]} submitted successfully.${NC}"
