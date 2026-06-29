#!/bin/bash
# create_vm.sh - Script to create pre-provisioned qcow2 and VDI images using QEMU and cloud-init

set -e

# Default values
FLAVOR=""
INSTALL_GRAPHICS="false"
REPO_URL="https://github.com/epics-training/training-vm.git"
REPO_BRANCH="main"
DISK_SIZE="150G"
VM_DIR="VMs"
CPUS="4"
CA_CERT=""
SET_CATRUST="false"

usage() {
    echo "Usage: $0 -f <flavor> [-j <cpus>] [-c <ca_cert>] [-g] [-r <repo_url>] [-b <branch>]"
    echo "  -f: flavor (fedora, rocky, debian, ubuntu)"
    echo "  -j: number of cpus to use (default: $CPUS)"
    echo "  -c: CA certificate to add (in PEM format)"
    echo "  -g: install graphics (default: false)"
    echo "  -r: repository URL (default: $REPO_URL)"
    echo "  -b: repository branch (default: $REPO_BRANCH)"
    exit 1
}

while getopts "f:j:c:gr:b:" opt; do
    case $opt in
        f) FLAVOR=$OPTARG ;;
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
        *) usage ;;
    esac
done

if [ -z "$FLAVOR" ]; then
    usage
fi

mkdir -p "$VM_DIR"
mkdir -p "cache"

case $FLAVOR in
    fedora)
        BASE_IMAGE_URL="https://download.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/x86_64/images/Fedora-Cloud-Base-Generic-44-1.7.x86_64.qcow2"
        BASE_IMAGE="cache/fedora-44.qcow2"
        ;;
    rocky)
        BASE_IMAGE_URL="https://dl.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud-Base.latest.x86_64.qcow2"
        BASE_IMAGE="cache/rocky-9.qcow2"
        ;;
    debian)
        BASE_IMAGE_URL="https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2"
        BASE_IMAGE="cache/debian-13.qcow2"
        ;;
    ubuntu)
        BASE_IMAGE_URL="https://cloud-images.ubuntu.com/resolute/current/resolute-server-cloudimg-amd64.img"
        BASE_IMAGE="cache/ubuntu-26.04.qcow2"
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

IMAGE_NAME="${FLAVOR}"
OUTPUT_QCOW2="${VM_DIR}/${IMAGE_NAME}.qcow2"
OUTPUT_VDI="${VM_DIR}/${IMAGE_NAME}.vdi"
SEED_ISO="seed.iso"

echo "Preparing disk image..."
cp "$BASE_IMAGE" "$OUTPUT_QCOW2"
qemu-img resize "$OUTPUT_QCOW2" "$DISK_SIZE"

echo "Generating cloud-init seed..."
# Create user-data from template
sed -e "s|TRAINING_VM_REPO=.*|TRAINING_VM_REPO=\"$REPO_URL\"|" \
    -e "s|TRAINING_VM_BRANCH=.*|TRAINING_VM_BRANCH=\"$REPO_BRANCH\"|" \
    -e "s|INSTALL_GRAPHICS=.*|INSTALL_GRAPHICS=\"$INSTALL_GRAPHICS\"|" \
    -e "s|SET_CATRUST=.*|SET_CATRUST=\"$SET_CATRUST\"|" \
    provisioning.sh > provisioning.sh.tmp

# We need to embed the script into user-data
cat <<EOF > user-data
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
$(sed '      s/^/      /' provisioning.sh.tmp)
EOF

if [[ ! -z "$CA_CERT" ]]; then
# Copy the cert for the catrust role
#   and use it for cloud-init
cat <<EOF >> user-data
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
cat <<EOF > meta-data
instance-id: i-$(date +%s)
local-hostname: ${FLAVOR}
EOF

cloud-localds "$SEED_ISO" user-data meta-data

echo "Launching QEMU for provisioning (this may take a while)..."
# Using -nographic for headless provisioning. The script will poweroff when done.
qemu-system-x86_64 \
    -cpu host \
    -M q35,accel=kvm:tcg \
    -m "$CPUS"G \
    -smp "$CPUS" \
    -parallel none \
    -drive file="$OUTPUT_QCOW2",if=virtio \
    -drive file="$SEED_ISO",format=raw,if=virtio \
    -nographic \
    -net nic,model=virtio -net user

echo "Provisioning finished. Cleaning up..."
rm "$SEED_ISO" user-data meta-data provisioning.sh.tmp

echo "Converting to VDI..."
qemu-img convert -O vdi "$OUTPUT_QCOW2" "$OUTPUT_VDI"

echo "Images created successfully in $VM_DIR:"
ls -lh "$OUTPUT_QCOW2" "$OUTPUT_VDI"
