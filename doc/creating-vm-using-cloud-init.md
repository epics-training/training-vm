# Create the VM Using Cloud-Init and QEMU

The Training-VM can be created automatically using cloud-init and QEMU. This process generates pre-provisioned images in qcow2 and VDI formats.

## Introduction

We provide a script `create_vm.sh` that automates the entire process:
1. Downloads a base cloud image for the selected distribution.
2. Prepares a cloud-init seed with provisioning instructions.
3. Launches a headless QEMU instance to run the Ansible provisioning.
4. Converts the resulting image to both qcow2 (for QEMU) and VDI (for VirtualBox).

## Pre-Requisites

Set up the required tools on your host machine:
- QEMU (specifically `qemu-system-x86_64` and `qemu-img`)
- cloud-image-utils (for `cloud-localds`)
- curl

On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install qemu-system-x86 qemu-utils cloud-image-utils curl
```

## Creating an Image

Supported flavors are: `fedora`, `rocky`, `debian`, `ubuntu`.

### Basic Usage

To create a minimal image without graphics:
```bash
./create_vm.sh -f rocky
```

### With Graphics

To create an image with the graphical subsystem (Gnome) installed:
```bash
./create_vm.sh -f rocky -g
```

### Custom Repository

If you want the VM to clone a specific fork or branch of the `training-vm` repository during provisioning:
```bash
./create_vm.sh -f rocky -r https://github.com/myuser/training-vm.git -b my-feature-branch
```

## Output

The resulting images are placed in the `VMs/` directory:
- `VMs/rocky.qcow2`: For use with QEMU or other KVM-based hypervisors.
- `VMs/rocky.vdi`: For use with VirtualBox.

## Troubleshooting

The provisioning happens headlessly. If you need to debug the process, you can modify `create_vm.sh` to remove the `-nographic` flag from the `qemu-system-x86_64` command, which will open a QEMU window where you can watch the console output.
