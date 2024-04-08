#!/bin/sh
# bootstrap.sh

# Simple bootstrap script for RedHat family systems (developed on Rocky 9)
# - installs prerequisites: git, ansible
# - clones training-vm repo into ./bootstrap

# $1 = repo (default: GitHub)

if [ "$(whoami)" == "root" ]; then
  echo "This script must be run by a regular user (with sudo privileges)."
  exit 1
fi

BOOTSTRAP_DIR="bootstrap"
BOOTSTRAP_REPO=${1:-"https://github.com/epics-training/training-vm"}

# Install prerequisites: Git, Ansible
if ! command -v git >/dev/null; then
    packages="git "
fi
if ! command -v ansible >/dev/null; then
    packages="${packages}ansible"
fi
if [ "${packages}" ]; then    
    echo "Installing prerequisites: ${packages}..."
    sudo dnf update
    sudo dnf install -y ${packages}
else
    echo "All prerequisites are installed."
fi

# Clone the training-vm bootstrap
if [ ! -e "${BOOTSTRAP_DIR}" ]; then
    echo "Cloning training-vm configuration into ./${BOOTSTRAP_DIR}..."
    git clone ${BOOTSTRAP_REPO} ${BOOTSTRAP_DIR}
else
    echo "You can update the existing training-vm configuration using 'git pull'."
fi

# Point out missing local.yml configuration
if [ ! -e "${BOOTSTRAP_DIR}/ansible/group_vars/local.yml" ]; then
    echo "Inside ${BOOTSTRAP_DIR}/ansible/group_vars create a local configuration file local.yml"
    echo "by making a copy of local.yml.sample and editing to your needs."
else
    echo "Verify your existing local configuration in ${BOOTSTRAP_DIR}/ansible/group_vars/local.yml"
fi

echo "Run ${BOOTSTRAP_DIR}/update.sh to update your system."
