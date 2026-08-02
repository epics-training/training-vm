#!/bin/bash
# create_vm.sh - Script to create pre-provisioned qcow2 and VDI images using QEMU and cloud-init

set -e

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=qemu_arch.sh
source "$SCRIPT_DIR/qemu_arch.sh"

# Default values
FLAVOR=""
ARCH=""
INSTALL_GRAPHICS="false"
REPO_URL="https://github.com/epics-training/training-vm.git"
REPO_BRANCH="main"
REPO_SHA=""
DISK_SIZE="150G"
VM_DIR="VMs"
CPUS="4"
CA_CERT=""
SET_CATRUST="false"
INSTALL_TEST_HOOK="false"

usage() {
    echo "Usage: $0 -f <flavor> [-a <arch>] [-j <cpus>] [-c <ca_cert>] [-g] [-r <repo_url>] [-b <branch>] [-T]"
    echo "  -f: flavor (fedora, rocky, debian, ubuntu)"
    echo "  -a: target architecture: x86_64 (amd64) or aarch64 (arm64)"
    echo "      (default: this host's architecture, currently $(host_arch))"
    echo "      A target differing from the host is emulated - correct, but slow."
    echo "  -j: number of cpus to use (default: $CPUS)"
    echo "  -c: CA certificate to add (in PEM format)"
    echo "  -g: install graphics (default: false)"
    echo "  -r: repository URL (default: $REPO_URL)"
    echo "  -b: repository branch (default: $REPO_BRANCH)"
    echo "  -s: repository commit sha to check out after cloning (default: branch tip)"
    echo "  -T: authorize the CI test SSH key for epics-dev (used by run_ansible_test.sh;"
    echo "      do not use for images meant for distribution)"
    exit 1
}

while getopts "f:a:j:c:gr:b:s:T" opt; do
    case $opt in
        f) FLAVOR=$OPTARG ;;
        a) ARCH=$OPTARG ;;
        j) if [[ $OPTARG =~ ^[1-9][0-9]*$ ]]; then
             CPUS=$OPTARG
           fi ;;
        c) if [ -f "$OPTARG" ]; then
             CA_CERT=$OPTARG
             SET_CATRUST="true"
           fi ;;
        g) INSTALL_GRAPHICS="true" ;;
        r) REPO_URL=$OPTARG ;;
        b) REPO_BRANCH=$OPTARG ;;
        s) REPO_SHA=$OPTARG ;;
        T) INSTALL_TEST_HOOK="true" ;;
        *) usage ;;
    esac
done

if [ -z "$FLAVOR" ]; then
    usage
fi

ARCH=$(normalize_arch "${ARCH:-$(uname -m)}") || exit 1
# Some distros name their images after the dpkg architecture instead
DEB_ARCH=$([ "$ARCH" = "x86_64" ] && echo "amd64" || echo "arm64")

mkdir -p "$VM_DIR"
mkdir -p "cache"

case $FLAVOR in
    fedora)
        BASE_IMAGE_URL="https://download.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/${ARCH}/images/Fedora-Cloud-Base-Generic-44-1.7.${ARCH}.qcow2"
        BASE_IMAGE="cache/fedora-44-${ARCH}.qcow2"
        ;;
    rocky)
        BASE_IMAGE_URL="https://dl.rockylinux.org/pub/rocky/9/images/${ARCH}/Rocky-9-GenericCloud-Base.latest.${ARCH}.qcow2"
        BASE_IMAGE="cache/rocky-9-${ARCH}.qcow2"
        ;;
    debian)
        BASE_IMAGE_URL="https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-${DEB_ARCH}.qcow2"
        BASE_IMAGE="cache/debian-13-${ARCH}.qcow2"
        ;;
    ubuntu)
        BASE_IMAGE_URL="https://cloud-images.ubuntu.com/resolute/current/resolute-server-cloudimg-${DEB_ARCH}.img"
        BASE_IMAGE="cache/ubuntu-26.04-${ARCH}.qcow2"
        ;;
    *)
        echo "Unknown flavor: $FLAVOR"
        exit 1
        ;;
esac

# Download base image if not exists
if [ ! -f "$BASE_IMAGE" ]; then
    echo "Downloading base image for $FLAVOR..."
    curl -L -o "$BASE_IMAGE" "$BASE_IMAGE_URL"
fi

IMAGE_NAME="${FLAVOR}-${ARCH}"
OUTPUT_QCOW2="${VM_DIR}/${IMAGE_NAME}.qcow2"
OUTPUT_VDI="${VM_DIR}/${IMAGE_NAME}.vdi"

# Scratch space for the cloud-init seed and (on aarch64) the guest's writable
# UEFI variable store, so nothing is left lying around in the working directory.
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
SEED_ISO="$WORK_DIR/seed.iso"

echo "Preparing disk image..."
cp "$BASE_IMAGE" "$OUTPUT_QCOW2"
qemu-img resize "$OUTPUT_QCOW2" "$DISK_SIZE"

echo "Generating cloud-init seed..."
# Create user-data from template
sed -e "s|TRAINING_VM_REPO=.*|TRAINING_VM_REPO=\"$REPO_URL\"|" \
    -e "s|TRAINING_VM_BRANCH=.*|TRAINING_VM_BRANCH=\"$REPO_BRANCH\"|" \
    -e "s|TRAINING_VM_SHA=.*|TRAINING_VM_SHA=\"$REPO_SHA\"|" \
    -e "s|INSTALL_GRAPHICS=.*|INSTALL_GRAPHICS=\"$INSTALL_GRAPHICS\"|" \
    -e "s|SET_CATRUST=.*|SET_CATRUST=\"$SET_CATRUST\"|" \
    -e "s|INSTALL_TEST_HOOK=.*|INSTALL_TEST_HOOK=\"$INSTALL_TEST_HOOK\"|" \
    provisioning.sh > "$WORK_DIR/provisioning.sh.tmp"

# We need to embed the script into user-data
cat <<EOF > "$WORK_DIR/user-data"
#cloud-config
runcmd:
  - /root/provisioning.sh

growpart:
  devices: [/]
resize_rootfs: true

write_files:
  - path: /root/provisioning.sh
    permissions: '0755'
    content: |
$(sed '      s/^/      /' "$WORK_DIR/provisioning.sh.tmp")
EOF

if [[ ! -z "$CA_CERT" ]]; then
# Copy the cert for the catrust role
#   and use it for cloud-init
cat <<EOF >> "$WORK_DIR/user-data"
  - path: /tmp/corporate_root_ca.crt
    content: |
$(sed '      s/^/      /' ${CA_CERT})

ca_certs:
  trusted:
  - |
$(sed '    s/^/    /' ${CA_CERT})
EOF

fi

# Meta-data
cat <<EOF > "$WORK_DIR/meta-data"
instance-id: i-$(date +%s)
local-hostname: ${FLAVOR}
EOF

cloud-localds "$SEED_ISO" "$WORK_DIR/user-data" "$WORK_DIR/meta-data"

# Pick the emulator, machine type, CPU model and (on aarch64) UEFI firmware
# that match the target architecture.
qemu_setup "$ARCH" "$WORK_DIR"

echo "Launching QEMU for provisioning of a $ARCH guest (this may take a while)..."
# Using -nographic for headless provisioning. The script will poweroff when done.
"$QEMU_BIN" \
    "${QEMU_ARCH_ARGS[@]}" \
    -m "$CPUS"G \
    -smp "$CPUS" \
    -parallel none \
    -drive file="$OUTPUT_QCOW2",if=virtio \
    -drive file="$SEED_ISO",format=raw,if=virtio \
    -nographic \
    -net nic,model=virtio -net user

echo "Provisioning finished. Cleaning up..."

echo "Converting to VDI..."
qemu-img convert -O vdi "$OUTPUT_QCOW2" "$OUTPUT_VDI"

echo "Images created successfully in $VM_DIR:"
ls -lh "$OUTPUT_QCOW2" "$OUTPUT_VDI"
