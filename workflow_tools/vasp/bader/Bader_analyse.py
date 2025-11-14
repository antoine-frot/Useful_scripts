#!/usr/bin/python3
"""
Bader Charge Analysis Results Processor

This script analyzes the results from VASP Bader charge analysis calculations.
It reads structure information from CONTCAR/POSCAR files and Bader analysis 
results from ACF files, then calculates and displays:
- Average Bader charges per atom type
- Magnetic moments per atom type  
- Statistical information (min, max, standard deviation)

The script automatically falls back to POSCAR if CONTCAR is missing or corrupted.
"""

import os
import statistics
import sys

def read_structure_file(filename):
    """
    Read VASP structure file (CONTCAR or POSCAR) and extract atom types and numbers.
    Returns tuple: (TYP_at, NB_at, filename_used)
    Raises exception if file cannot be read or is improperly formatted.
    """
    try:
        with open(filename, "r") as file:
            lines = file.readlines()
        
        if len(lines) < 7:
            raise ValueError(f"{filename} file has only {len(lines)} lines, but at least 7 are required")
        
        TYP_at = lines[5].split()
        NB_at = lines[6].split()
        
        if not TYP_at or not NB_at:
            raise ValueError(f"Line 6 or 7 in {filename} is empty or improperly formatted")
        
        NB_at = [int(element) for element in NB_at]
        
        return TYP_at, NB_at, filename
        
    except Exception as e:
        raise Exception(f"Error reading {filename}: {e}")

# Try to read structure file with fallback
TYP_at = None
NB_at = None
poscar_file = None

# First try CONTCAR
if os.path.exists("CONTCAR"):
    try:
        TYP_at, NB_at, poscar_file = read_structure_file("CONTCAR")
    except Exception as e:
        print(f"Warning: {e}")
        if os.path.exists("POSCAR"):
            try:
                TYP_at, NB_at, poscar_file = read_structure_file("POSCAR")
            except Exception as e2:
                print(f"Error: Both CONTCAR and POSCAR failed: {e2}")
                sys.exit(1)
        else:
            print("Error: No POSCAR backup available")
            sys.exit(1)
elif os.path.exists("POSCAR"):
    try:
        TYP_at, NB_at, poscar_file = read_structure_file("POSCAR")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
else:
    print("Error: Neither CONTCAR nor POSCAR file found in current directory")
    sys.exit(1)

print("Atomes :", TYP_at)
print("Stoichiometry :", NB_at)

column_5chg_values = []
column_5mag_values = []
try:
    with open("ACF_chg.dat", "r") as file:
        # Lire les lignes du fichier à partir de la troisième ligne
        lines = file.readlines()[2:]
        for line in lines:
            elements = line.split()
            if len(elements)==1:
                break
            column_5chg_value = float(elements[4])
            column_5chg_values.append(column_5chg_value)

except Exception as e:
    print(f"Error reading ACF_chg.dat file: {e}")
    sys.exit(1)

try:
    with open("ACF_mag.dat", "r") as file:
        lines = file.readlines()[2:]
        for line in lines:
            elements = line.split()
            if len(elements)==1:
                break
            column_5mag_value = float(elements[4])  # Convertir en float si nécessaire
            column_5mag_values.append(column_5mag_value)

except Exception as e:
    print(f"Error reading ACF_mag.dat file: {e}")
    sys.exit(1)

nb_at_maille=0
for NB in NB_at:
     nb_at_maille=nb_at_maille+NB
print("Nombre d'atomes par maille :",nb_at_maille)

# Calculer et afficher les valeurs moyennes des charges et moments magnétiques par atome
print("") 
print("------------------------------") 
print("Populations de Bader par Atome")
print("------------------------------") 
index_nb=0
index_typ=0
for NB in NB_at:
    print(TYP_at[index_typ],sum(column_5chg_values[index_nb:index_nb+NB])/NB)
    print("Bader Min :", min(column_5chg_values[index_nb:index_nb+NB]))
    print("Bader Max :", max(column_5chg_values[index_nb:index_nb+NB]))
    print("RMSD :", statistics.stdev(column_5chg_values[index_nb:index_nb+NB]))
    print("-------------------------------") 
    index_typ=index_typ+1
    index_nb=index_nb+NB

print("") 
print("------------------------------") 
print("Moments Magnétiques par Atome")
print("------------------------------") 
index_nb=0
index_typ=0
for NB in NB_at:
    print(TYP_at[index_typ],sum(column_5mag_values[index_nb:index_nb+NB])/NB)
    print("MagM Min :", min(column_5mag_values[index_nb:index_nb+NB]))
    print("MagM Max :", max(column_5mag_values[index_nb:index_nb+NB]))
    print("RMSD :", statistics.stdev(column_5mag_values[index_nb:index_nb+NB]))
    print("-------------------------------")

    index_typ=index_typ+1
    index_nb=index_nb+NB

