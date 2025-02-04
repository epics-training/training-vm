#!/bin/bash
# bootstrap.sh

# Simple bootstrap script for training VM systems
# - reads local settings
# - installs prerequisites: git, ansible
# - clones collection repo into collection subdir (with submodules)
# - creates/links Ansible configuration local.yml

# $1 = settings file (default: ./bootstrap_setup or ~/bootstrap_setup)

if [ "$(whoami)" == "root" ]; then
    echo "This script must be run by a regular user (with sudo privileges)."
    exit 1
fi

# Read configuration file "$1", ./bootstrap_setup or ~/bootstrap_setup
echo -n "Reading configuration"
if [ "$1" ]; then
    if [ -e "$1" ]; then 
        source "$1"
        echo " from $1"
    else
        echo " [ERROR: file $1 not found]"
        exit 1
    fi    
elif [ -e ./bootstrap_setup ]; then
    source ./bootstrap_setup
    echo " from ./bootstrap_setup"
elif [ -e ~/bootstrap_setup ]; then
    source ~/bootstrap_setup
    echo " from ~/bootstrap_setup"
fi

COLLECTION=${COLLECTION:-"training"}
SLUGFILE=${SLUGFILE:-"/etc/epics-training"}

COLLECTION_REPO=${COLLECTION_REPO:-"https://github.com/epics-training/training-collection"}
# Replace collection submodule with direct clone (development)
VM_REPO=${VM_REPO:-none}

# if SLUG is not set, read it from SLUGFILE or ask for it
if [ ! "${SLUG}" ]; then
    if [ ! -e "${SLUGFILE}" ]; then
        echo "Please specify the slug (short name) of the event that you"
        echo "want to configure this machine for."
        echo "See ${COLLECTION_REPO} branches for valid strings."
        echo "Leaving it empty will use the default branch with all available submodules."
        echo "(This is recommended for development of the setup.)"
        echo "The slug will be written to ${SLUGFILE}."
        read -p "Event name []: " SLUG
        TMP_FILE=$(mktemp -q /tmp/epics.XXXXXX)
        echo "$SLUG" > $TMP_FILE
        sudo cp $TMP_FILE ${SLUGFILE}
        sudo chmod 644 ${SLUGFILE}
    else
        SLUG=$(<${SLUGFILE})
    fi
fi

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

# Clone the collection
if [ ! -e "${COLLECTION}" ]; then
    branch=""
    if [ "$SLUG" ]; then
        branch="-b $SLUG"
    fi
    echo "Cloning collection (for $SLUG) into ./${COLLECTION}..."
    git clone --recurse-submodules $branch ${COLLECTION_REPO} ${COLLECTION}
else
    echo "Update the existing VM configuration by running 'git pull' in ./${COLLECTION_DIR}."
    echo "Switch the setup with 'git checkout \$(<${SLUGFILE})' in ./${COLLECTION_DIR}."
fi

# Optional: switch to direct vm-setup clone
if [ "${VM_REPO}" != "none" ]; then
    echo "Switching vm-setup submodule to a clone of ${VM_REPO}..."
    ( cd ${COLLECTION}; git rm vm-setup; git commit -m "bootstrap.sh: remove submodule vm-setup" )
    git clone ${VM_REPO} ${COLLECTION}/vm-setup
fi

# Point out missing local.yml configuration
if [ ! -e "${COLLECTION}/vm-setup/ansible/group_vars/local.yml" ]; then
    if [ ! -e "${COLLECTION}/local.yml" ]; then
        echo "No local configuration found. Creating one from local.yml.sample"
        cp "${COLLECTION}/vm-setup/ansible/group_vars/local.yml.sample" "${COLLECTION}/local.yml"
    fi
    ln -s "../../../local.yml" "${COLLECTION}/vm-setup/ansible/group_vars/local.yml"
else
    echo -n "Verify your existing local configuration"
    if [ -h "${COLLECTION}/vm-setup/ansible/group_vars/local.yml" ]; then
        echo " in ${COLLECTION}/local.yml"
    else
        echo " in ${COLLECTION}/vm-setup/ansible/group_vars/local.yml"
    fi
fi

echo "Run ${COLLECTION}/vm-setup/update.sh at any time to finish or update your installation."
