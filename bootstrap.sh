#!/bin/bash
# bootstrap.sh

# Bootstrap script for training-vm based systems
# - reads local settings
# - installs prerequisites: git, ansible
# - clones collection repo into collection subdir (with submodules)
# - creates/links Ansible configuration local.yml

# $1 = settings file (default: ./bootstrap_setup or ~/bootstrap_setup)

if [ "$(whoami)" == "root" ]; then
    echo "This script must be run by a regular user (with sudo privileges)."
    exit 1
fi

# Associative arrays to configure developer mode
declare -A REPO BRANCH

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

# Override these defaults in your 'bootstrap_setup' file
# Switch submodule $COLLECTION/xyz to direct checkout by setting
# REPO[xyz] (and BRANCH[xyz]
COLLECTION=${COLLECTION:-"training"}
SLUGFILE=${SLUGFILE:-"/etc/epics-training"}
COLLECTION_REPO=${COLLECTION_REPO:-"https://github.com/epics-training/training-collection"}

# if SLUG is not set, read it from SLUGFILE or ask for it
if [ ! "${SLUG}" ]; then
    if [ ! -e "${SLUGFILE}" ]; then
        echo "Please specify the slug (short name) of the event that you"
        echo "want to configure this machine for."
        echo "See ${COLLECTION_REPO} branches for valid strings."
        echo "Leaving it empty will use the default branch with all available submodules."
        echo "For development, you can switch submodules to use direct checkouts"
        echo "through settings in the 'bootstrap_setup' file."
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
    packages="git"
fi
if ! command -v ansible >/dev/null; then
    packages="${packages} ansible"
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
    git clone $branch ${COLLECTION_REPO} ${COLLECTION}
else
    echo "Update the existing VM configuration by running 'git pull' in ./${COLLECTION_DIR}."
    echo "Switch the setup with 'git checkout \$(<${SLUGFILE})' in ./${COLLECTION_DIR}."
fi

cd ${COLLECTION}
modules=$(git submodule | awk '{ print $2 }')

echo "Adding submodules into ${COLLECTION} ..."

for mod in ${modules}; do
    repo="${REPO[${mod}]}"
    branch="${BRANCH[${mod}]}"
    if [ "$repo" ]; then
        if [ "$branch" ]; then
            extra="-b $branch"
        fi
        echo "Removing submodule $mod ..."
        git submodule deinit -f $mod
        rm -rf .git/modules/$mod $mod
        git rm -f $mod
        echo "Cloning $mod from $repo ..."
        git clone $extra $repo $mod
    else
        git submodule update --init $mod
    fi
done

# Point out missing local.yml configuration
if [ ! -e "vm-setup/ansible/group_vars/local.yml" ]; then
    if [ ! -e "local.yml" ]; then
        echo "No local configuration found. Creating one from local.yml.sample"
        cp "vm-setup/ansible/group_vars/local.yml.sample" "local.yml"
    fi
    ln -s "../../../local.yml" "vm-setup/ansible/group_vars/local.yml"
else
    echo -n "Verify your existing local configuration"
    if [ -h "vm-setup/ansible/group_vars/local.yml" ]; then
        echo " in ${COLLECTION}/local.yml"
    else
        echo " in ${COLLECTION}/vm-setup/ansible/group_vars/local.yml"
    fi
fi

echo "Run ${COLLECTION}/vm-setup/update.sh at any time to finish or update your installation."
