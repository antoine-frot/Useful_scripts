#!/bin/bash
# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

#export INPUTS="INCAR POSCAR POTCAR KPOINTS VASP_version.txt"
INPUTS="INCAR POSCAR POTCAR KPOINTS VASP_version.txt"
local=afrot@coloquinte.d5.icgm.fr:/home/afrot
alias activate="source $HOME/virtual_env_python/bin/activate"
activate
