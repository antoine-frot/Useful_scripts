# Got to the directory you want to copy and run this script
dir=$(pwd)
main_dir=$(dirname $dir)
rsync -avz --rsync-path="mkdir -p $main_dir && rsync" $dir afrot@Coloquinte.d5.icgm.fr:$main_dir

