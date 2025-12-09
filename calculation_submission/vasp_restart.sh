#!/bin/bash
if [ -f CONTCAR ]; then
    if [ ! -f POSCAR_ini ]; then
        mv POSCAR POSCAR_ini
        if [ $? -ne 0 ] || [ ! -f POSCAR_ini ]; then
            echo "Error: POSCAR file not found and cannot rename to POSCAR_ini. Aborting."
            exit 1
        fi
    fi
    cp CONTCAR POSCAR
    if [ $? -ne 0 ] || [ ! -f POSCAR ]; then
        echo "Error: Failed to create POSCAR from CONTCAR. Aborting."
        exit 1
    fi
fi
submit_vasp
