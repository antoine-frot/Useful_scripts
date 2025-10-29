#!/usr/bin/python3

import os
import statistics
cwd = os.getcwd()
print("")
print("")
print("************************************************")
print(cwd)
print("")

# Ouvrir les fichiers CONTCAR et ACF_chg.dat en mode lecture
with open("CONTCAR", "r") as file:
    # Lire les lignes du fichier
    lines = file.readlines()

# Récupérer la septième ligne 
TYP_at = lines[5].split()
NB_at = lines[6].split()

# Convertir les éléments en float et les stocker dans le vecteur A
NB_at = [int(element) for element in NB_at]

# Afficher le vecteur A
#print("Vecteur TYP_at:", TYP_at)
print("Atomes :", TYP_at)
print("Stoichiometry :", NB_at)

# Initialiser une liste pour stocker les valeurs de la colonne 5
column_5chg_values = []
column_5mag_values = []

# Ouvrir le fichier ACF_chg.dat en mode lecture
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

#
# Ouvrir le fichier ACF_chg.dat en mode lecture
#
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

