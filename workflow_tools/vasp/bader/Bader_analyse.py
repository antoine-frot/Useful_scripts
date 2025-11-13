#!/usr/bin/python3

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
        
        # Vérifier que le fichier a assez de lignes
        if len(lines) < 7:
            raise ValueError(f"{filename} file has only {len(lines)} lines, but at least 7 are required")
        
        # Récupérer la sixième et septième ligne
        TYP_at = lines[5].split()
        NB_at = lines[6].split()
        
        # Vérifier que les lignes ne sont pas vides
        if not TYP_at or not NB_at:
            raise ValueError(f"Line 6 or 7 in {filename} is empty or improperly formatted")
        
        # Convertir les nombres d'atomes en entiers
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
                print("Using POSCAR for structure information")
            except Exception as e2:
                print(f"Error: Both CONTCAR and POSCAR failed: {e2}")
                sys.exit(1)
        else:
            print("Error: No POSCAR backup available")
            sys.exit(1)
elif os.path.exists("POSCAR"):
    try:
        TYP_at, NB_at, poscar_file = read_structure_file("POSCAR")
        print("CONTCAR not found, using POSCAR for structure information")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
else:
    print("Error: Neither CONTCAR nor POSCAR file found in current directory")
    sys.exit(1)

# Afficher le vecteur A
#print("Vecteur TYP_at:", TYP_at)
print("Atomes :", TYP_at)
print("Stoichiometry :", NB_at)

# Initialiser une liste pour stocker les valeurs de la colonne 5
column_5chg_values = []
column_5mag_values = []

# Ouvrir le fichier ACF_chg.dat en mode lecture
try:
    with open("ACF_chg.dat", "r") as file:
        # Lire les lignes du fichier à partir de la troisième ligne
        lines = file.readlines()[2:]
        for line in lines:
            # Diviser la ligne en éléments (supposons qu'ils sont séparés par des espaces)
            elements = line.split()
            if len(elements)==1:
                break

            # Récupérer la cinquième colonne 
            column_5chg_value = float(elements[4])

            # Ajouter la valeur de la cinquième colonne à la liste
            column_5chg_values.append(column_5chg_value)

except Exception as e:
    print(f"Error reading ACF_chg.dat file: {e}")
    sys.exit(1)

#
# Ouvrir le fichier ACF_chg.dat en mode lecture
#
try:
    with open("ACF_mag.dat", "r") as file:
        # Lire les lignes du fichier à partir de la troisième ligne
        lines = file.readlines()[2:]

        # Parcourir les lignes à partir de la troisième ligne
        for line in lines:
            # Diviser la ligne en éléments (supposons qu'ils sont séparés par des espaces)
            elements = line.split()
            if len(elements)==1:
                break
    #        print(elements)

            # Récupérer la cinquième colonne (l'index est 4 car les index commencent à 0)
            column_5mag_value = float(elements[4])  # Convertir en float si nécessaire
            # Ajouter la valeur de la cinquième colonne à la liste
            column_5mag_values.append(column_5mag_value)

except Exception as e:
    print(f"Error reading ACF_mag.dat file: {e}")
    sys.exit(1)

# Afficher les valeurs de la colonne 5 du premier fichier puis du second avec en première ligne le path répertoire

# Calcul du nombre d'atomes par maille pour connaître le nombre de valeurs de chg ou mag au total pour le calcul de l'écart type
#
nb_at_maille=0
for NB in NB_at:
     nb_at_maille=nb_at_maille+NB
print("Nombre d'atomes par maille :",nb_at_maille)
#
#
# Calculer et afficher les valeurs moyennes des charges et moments magnétiques par atome
#
print("") 
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

#
print("") 
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

