#!/bin/bash
# provisioning.sh - One-off initialization script for cloud-init

set -xe

# These variables are set by the create_vm.sh script
TRAINING_VM_REPO="WILL BE SET BY create_vm.sh"
TRAINING_VM_BRANCH="WILL BE SET BY create_vm.sh"
INSTALL_GRAPHICS="WILL BE SET BY create_vm.sh"
SET_CATRUST="WILL BE SET BY create_vm.sh"

# Can be set through environment
ANSIBLE_ARGS="${ANSIBLE_ARGS:-}"

# Determine installer
if command -v apt-get >/dev/null; then
    installer="apt"
elif command -v dnf >/dev/null; then
    installer="dnf"
else
    echo "Unknown installer"
    exit 1
fi

# Install Ansible and Git
if [[ "$installer" == "apt" ]]; then
    export DEBIAN_FRONTEND=noninteractive
    cat > /etc/apt/apt.conf.d/01norecommend << EOF
APT::Install-Recommends "0";
APT::Install-Suggests "0";
EOF
    apt-get update
    apt-get install -y git ansible-core python3-jmespath
elif [[ "$installer" == "dnf" ]]; then
    dnf install -y git ansible-core python3-jmespath
fi

# Clone the training-vm repo
# This clone is only used while creating the VM.
# The final bootstrap clones a training collection
mkdir -p /opt/vm-setup
git clone -b "$TRAINING_VM_BRANCH" "$TRAINING_VM_REPO" /opt/vm-setup/training-vm

cd /opt/vm-setup/training-vm/ansible

# Install dependencies
ansible-galaxy install -r requirements.yml || true

# Run the playbook
# We pass install_graphics and initial_setup=true
ansible-playbook playbook.yml \
    -e @vars/local.yml \
    -e "initial_setup=true" \
    -e "install_graphics=$INSTALL_GRAPHICS" \
    -e "catrust=$SET_CATRUST" \
    $ANSIBLE_ARGS

# Remove the cloned training-vm repo
rm -fr /opt/vm-setup

# Signal completion and shutdown
# We use a flag file that the host can poll for if needed, or just shutdown.
echo "Provisioning complete" > /var/log/provisioning_complete
poweroff
