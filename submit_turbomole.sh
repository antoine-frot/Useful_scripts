#!/bin/bash
shopt -s nullglob

: '
Module: submit_turbomole.sh
Description:
    This script automates the preparation and submission of TURBOMOLE quantum chemical calculation jobs
    via SLURM. It expects exactly one input file (*.input), one or more geometry files (*.xyz) and one 
    submission script in the current directory.

    For each *.xyz file, the script will:
      - Create a dedicated directory (named after the geometry file without its extension).
      - Construct a job directory named by combining the *.xyz filename and the *.inp filename.
      - Convert the .xyz file to TURBOMOLE coord format using x2t.
      - Run define using the provided input file to set up the calculation.
      - Optionally insert custom directives from insert_*.txt files into the control file.
      - Submit the job using a SLURM submission script.
      - Remove original input files after successful submission (user configurable).
    
Usage:
    Place one *.input file (use with define), one or more *.xyz files, 
    along with a SLURM submission script named "sub_tm_psmn.sh". Execute:
        ./submit_turbomole.sh
'

# --- Define Color Variables ---
NC='\033[0m'         # No Color
R='\033[0;31m'       # Red
G='\033[0;32m'       # Green
Y='\033[0;33m'       # Yellow
M='\033[0;35m'       # Magenta

# --- Set Variables ---
Input_directory='Input_Turbomole'
submission_script="sub_tm_psmn.sh"

# --- Set the Working Directory ---
root_dir=$(pwd)
echo -e "${Y}You are in the directory ${root_dir}.${NC}"

# --- Set TURBOMOLE variables ---
export TURBODIR='/home/jtoldo/softs/TmoleX2024/TURBOMOLE'
export TURBOMOLE_SYSNAME=em64t-unknown-linux-gnu_smp
export PATH=$PATH:$TURBODIR/scripts
export PATH=$PATH:$TURBODIR/bin/`sysname`
source ${TURBODIR}/Config_turbo_env

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
input_files=( *.input )
if (( ${#input_files[@]} != 1 )); then
    echo -e "${R}Error: Exactly one input file (*.input) is expected in the current directory (currently ${input_files[@]} are given).${NC}"
    exit 1
fi
input="${input_files[0]}"

# Require at least one *.xyz file
xyz_files=( *.xyz )
if (( ${#xyz_files[@]} == 0 )); then
    echo -e "${R}Error: No xyz files found in the current directory.${NC}"
    exit 1
fi

# Inform the user about the number of .xyz files found
if (( ${#xyz_files[@]} == 1 )); then
  echo -e "${G}Found 1 xyz file (${xyz_files[@]}).${NC}"
else
  echo -e "${G}Found ${M}${#xyz_files[@]}${G} xyz files.${NC}"
fi

# Require exactly one *.inp file in the current directory
if [[ ! -f $submission_script ]]; then
    echo -e "${R}Error: $submission_script not found in the current directory.${NC}"
    exit 1
fi

# Inform the user about insert-*.txt files found
insert_files=( insert_*.txt)
if (( ${#insert_files[@]} != 0 )); then
    echo -e "${G}${insert_files[@]} found in the current directory.${NC}"
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
ask_overwrite=0       # Flag to stop prompting the user repeatedly
ask_sameparameter=0       # Flag to stop prompting the user repeatedly
submitted=0

# --- Process Each .xyz File ---
for xyz_file in "${xyz_files[@]}"; do
  # Create a subdirectory named after the .xyz file (without its extension)
  molecule_no_ext="${xyz_file%.*}"
  xyz_dir="${root_dir}/${molecule_no_ext%%-*}"
  mkdir -p "$xyz_dir"
  
  # Enter the xyz_dir directory
  pushd "$xyz_dir" > /dev/null
  
  # Construct job basename combining the .xyz filename and the input file name (both without extensions)
  job_basename="${xyz_file%.*}-${input%.*}"
  job_directory="${PWD}/${job_basename}"
  
  # If the job directory already exists, handle parameter reuse or prompt the user.
  if [ -d "$job_directory" ]; then
    echo -e "${R}Directory $(basename "$job_directory") already exists.${NC}"
    
    # Ask before overwritting
    if (( ask_overwrite == 0 )); then
      if prompt_yes_no "Do you want to overwrite the directory"; then
        overwrite_dirs=0
      else
        overwrite_dirs=1
      fi
    fi

    # Ask the user if it want keep the same response as just asked
    if [ "$two_existing_dir" -eq 0 ]; then
      if prompt_yes_no "Do you want to keep the same parameter for all existing directories"; then
        ask=1
      fi
      two_existing_dir=1
    fi

    # Don't overwrite if asked
    if [ "$overwrite_dirs" -eq 1 ]; then
      echo -e "${Y}Skipping $xyz_file.${NC}"
      popd > /dev/null
      continue
    else
      rm "$job_directory"/control
    fi

  else
    mkdir -p "$job_directory"
  fi 

  pushd "$job_directory" > /dev/null
  cp "${root_dir}/${input}" .
  cp "${root_dir}/${submission_script}" .
  cp "${root_dir}/${xyz_file}" .
  for file in "${insert_files[@]}"; do
    cp "${root_dir}/${file}" .
  done


  # --- Prepare TURBOMOLE input files ---
  # Process geometry file
  if ! x2t "${xyz_file}" > coord; then
      echo -e "${R}Error converting $xyz_file to coord${NC}"
      exit 1
  fi

  # Run define
  define < "${input}" > /dev/null

  # Insert custom directives
  if (( ${#insert_files[@]} > 0 )); then
      head -n -1 control > temp_head
      tail -n 1 control > temp_tail
      cat temp_head "${insert_files[@]}" temp_tail > control
      rm temp_head temp_tail
  fi
  
  # Submit the job via SLURM
  if ! sbatch --job-name="$job_basename" "${submission_script}" >/dev/null; then
      echo -e "${R}Submission failed for $job_name.${NC}"
      exit 1
  fi
  (( submitted += 1 ))
  echo -e "${G}$job_basename has been submitted.${NC}"
  sleep 1
  
  rm "${root_dir}/${xyz_file}"
  # Return to the xyz directory and then to the root directory
  popd > /dev/null  # Exit job directory
  popd > /dev/null  # Exit xyz_dir
done

if [ $submitted == 0 ]; then
  echo -e "${R}No file submitted.${NC}"
  exit 1
else
  echo -e "${G}$submitted submitted successfully.${NC}"
fi

# Keep the input files in Input_directory
if prompt_yes_no "Do you want to keep the input file ($input)?"; then
  mkdir -p "${root_dir}/$Input_directory"
  mv "${root_dir}/${input}" "${root_dir}/$Input_directory/${input}"
  echo -e "${G}${input} stored in $Input_directory.${NC}"
else
  rm "${root_dir}/${input}"
fi

if prompt_yes_no "Do you want to keep the submission script ($submission_script)?"; then
  mkdir -p "${root_dir}/$Input_directory"
  mv "${root_dir}/${submission_script}" "${root_dir}/$Input_directory/${submission_script}"
  echo -e "${G}${submission_script} stored in $Input_directory.${NC}"
else
  rm "${root_dir}/${submission_script}"
fi

if (( ${#insert_files[@]} > 0 )); then
  for insert_file in "${insert_files[@]}"
  do
    if prompt_yes_no "Do you want to keep $insert_file ?"; then
      mkdir -p "${root_dir}/$Input_directory"
      mv "${root_dir}/${insert_file}" "${root_dir}/$Input_directory/${insert_file}"
      echo -e "${G}${insert_file} stored in $Input_directory.${NC}"
    else
      rm "${root_dir}/${insert_file}"
    fi
  done
fi
