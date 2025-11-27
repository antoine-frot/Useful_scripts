!#/usr/bin/bash
cd $HOME
rsync -av --max-size=5000000 manganese_oxyde ruthenium_oxyde titanium_sulfide recycling Li Input_VASP Images/ CUBE.VASP/ afrot@sd5.icgm.fr:/home/afrot
