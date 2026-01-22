#!/bin/bash
# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

export INPUTS="INCAR POSCAR POTCAR KPOINTS VASP_version.txt"
OUTPUTS="INCAR POSCAR POTCAR KPOINTS VASP_version.txt WAVECAR CHGCAR"
local=afrot@coloquinte.d5.icgm.fr:/home/afrot
potentiels="/home/sol/Vasp/potentiels/potpaw_PBE.64"
alias activate="source $HOME/virtual_env_python/bin/activate"
activate
export PERL5LIB=$PERL5LIB:~/path/to/your/vtstscripts
