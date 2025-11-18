#!/bin/bash
# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

#export INPUTS="INCAR POSCAR POTCAR KPOINTS VASP_version.txt"
export INPUTS="INCAR POSCAR POTCAR KPOINTS VASP_version.txt"
local=afrot@coloquinte.d5.icgm.fr:/home/afrot
potentiels="/home/sol/Vasp/potentiels/potpaw_PBE.64"
alias activate="source $HOME/virtual_env_python/bin/activate"
activate
