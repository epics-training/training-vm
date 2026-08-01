#!/bin/bash
# provisioning.sh - One-off initialization script for cloud-init

set -xe

# Always power off when this script exits, success or failure, so a
# provisioning failure fails fast instead of leaving the VM idle
trap 'poweroff' EXIT

# These variables are set by the create_vm.sh script
TRAINING_VM_REPO="WILL BE SET BY create_vm.sh"
TRAINING_VM_BRANCH="WILL BE SET BY create_vm.sh"
TRAINING_VM_SHA="WILL BE SET BY create_vm.sh"
INSTALL_GRAPHICS="WILL BE SET BY create_vm.sh"
SET_CATRUST="WILL BE SET BY create_vm.sh"
INSTALL_TEST_HOOK="WILL BE SET BY create_vm.sh"

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

if [[ -n "$TRAINING_VM_SHA" ]]; then
    git -C /opt/vm-setup/training-vm checkout "$TRAINING_VM_SHA"
fi

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

# Authorize the CI test key for the epics-dev user (stage 2 of the qcow2/QEMU
# CI). This is the ONLY place cloud-init is involved in the role-test flow:
# it bakes SSH access into the image at build time so that stage-2 test boots
# (cloud-init/run_ansible_test.sh) never need to invoke cloud-init again -
# they just SSH in as epics-dev (the same user and privilege model - regular
# user, passwordless sudo via `become` - real bootstrap.sh/update.sh runs use)
# and run ansible-playbook directly. On a normal image (no -T) this key is
# never installed.
if [[ "$INSTALL_TEST_HOOK" == "true" ]]; then
    install -d -m 700 -o epics-dev -g epics-dev /home/epics-dev/.ssh
    install -m 600 -o epics-dev -g epics-dev /dev/null /home/epics-dev/.ssh/authorized_keys
    cat /opt/vm-setup/training-vm/cloud-init/ci_test_key.pub >> /home/epics-dev/.ssh/authorized_keys

    mkdir -p /etc/ssh/sshd_config.d
    cat > /etc/ssh/sshd_config.d/99-ci-test.conf << 'SSHD'
PubkeyAuthentication yes
SSHD

    systemctl enable --now sshd.service 2>/dev/null || systemctl enable --now ssh.service
fi

# Remove the cloned training-vm repo
rm -fr /opt/vm-setup

# Signal completion. The EXIT trap above handles the actual shutdown.
# We use a flag file that the host can poll for if needed.
echo "Provisioning complete" > /var/log/provisioning_complete
