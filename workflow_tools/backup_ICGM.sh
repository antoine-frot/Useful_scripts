#!/bin/bash
# Go to the directory you want to copy on the other hosts and run this script
dir=$(pwd)
main_dir=$(dirname "$dir")
hostnames=("Coloquinte.d5.icgm.fr" "taz")
current_hostname=$(hostname)
answer=true
while $answer; do
	read -n 1 -r -p "$(echo -e "Are you sure you want to backup $dir (y/n)?")" answer
	echo
	case "$answer" in
	    [yY]) answer=false ;;
	    [nN]) exit 0 ;;
	    *) echo -e "Please answer y or n." ;;
	esac
done

for hostname in "${hostnames[@]}"; do
  if [ "$hostname" != "$current_hostname" ]; then
    rsync -avz --exclude='WAVECAR' --rsync-path="mkdir -p $main_dir && rsync" "$dir" afrot@"$hostname":"$main_dir"
  fi
done
