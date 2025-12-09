# What Is This Repository About?
This repository contains all the scripts I write and use in my daily work as a computational chemist.
Its primary purpose is personal use, but I am doing my best to make it accessible and useful to a broader audience.

# Getting Started
## Installation
```bash
cd $HOME
git clone https://github.com/antoine-frot/Useful_scripts.git
``` 
## Set Up the Configuration Files (Essential)
Back up your current `.bashrc`:
```bash
cp ~/.bashrc .bashrc_backup
```
Install the new configuration files and append your previous `.bashrc` to the end of the new one:
```bash
cp bash_utility/configuration_files/bashrc ~/.bashrc
cat .bashrc_backup >> ~/.bashrc
```
> WARNING: If you cloned this repository somewhere other than your home directory, update the path to this git accordingly in the new .bashrc file.

You’re all set!

## Set Up Additional Configuration Files (Optional)
You can save your previous `.bashrc` under a machine-specific name:
```bash
cp ~/.bashrc bash_utility/configuration_files/bashrc_name_of_the_machine
```

Additional configuration files such as `.vimrc` and `.bash_profile` can also be installed:
```bash
for configuration_file in (bashrc bash_profile vimrc); do
    cp bash_utility/configuration_files/$configuration_file ~/.$configuration_file
done
```
After installing them, update the path to this repository and the name of the machine-specific .bashrc inside the main .bashrc file.


## Setting Up the SSH Key (For Personal Use Only)
```bash
ssh-keygen -t ed25519 -C "antoine.frot@orange.fr"   # Use default options
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
git remote set-url origin git@github.com:antoine-frot/Useful_scripts
```