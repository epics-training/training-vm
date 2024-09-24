#!/bin/sh
# update.sh

# Update script that tries to pull the training VM to the appropriate latest versions

# Improved robustness:
# - tries the first command line arg or "." as location for the collection
# - remaining command line args are passed through to ansible-playbook call

# - runs 'git pull --recurse-submodules' on the collection
# - runs ansible

collection_dir=${1%/}

if [ "$(whoami)" == "root" ]; then
  echo "This script must be run by a regular user (with sudo privileges)."
  exit 1
fi

if [ -d "${collection_dir}" ]; then
    shift
elif [ -d "./vm-setup/ansible" ]; then
    collection_dir="."
fi

bootstrap_dir=${collection_dir}/vm-setup

if [ ! -d ${bootstrap_dir}/ansible ]; then
    echo "update.sh [collection_dir] [ansible-playbook args...]"
    exit 1
fi

if [ -e "/etc/epics-training" ]; then
    slug=$(</etc/epics-training)
else
    slug=""
fi

if [ ! -e "${collection_dir}/vm-setup/ansible/group_vars/local.yml" ]; then
    ln -s "../../../local.yml" "${collection_dir}/vm-setup/ansible/group_vars/local.yml"
fi

ansible-galaxy install -r ${bootstrap_dir}/requirements.yml || true
ansible-playbook -i ${bootstrap_dir}/ansible/hosts ${bootstrap_dir}/ansible/playbook.yml "$@"
