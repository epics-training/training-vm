#!/bin/sh
# update.sh

# Simple caller script for ansible-playbook
# Improved robustness:
# - tries the first command line arg, then the script directory, then "." as location
# - remaining command line args are passed through to ansible-playbook call

bootstrap_dir=${1%/}
script_dir=$(dirname $0)

if [ "$(whoami)" == "root" ]; then
  echo "This script must be run by a regular user (with sudo privileges)."
  exit 1
fi

if [ -d "${bootstrap_dir}" ]; then
    shift
elif [ -d "${script_dir}" ]; then
    bootstrap_dir=${script_dir%/}
else
    bootstrap_dir="."
fi

if [ ! -d ${bootstrap_dir}/ansible ]; then
    echo "update.sh [bootstrap_dir] [ansible-playbook args...]"
    exit 1
fi

exec ansible-playbook -i ${bootstrap_dir}/ansible/hosts ${bootstrap_dir}/ansible/playbook.yml "$@"
