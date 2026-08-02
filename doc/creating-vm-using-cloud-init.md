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
- QEMU for the architecture you want to build for
  (`qemu-system-x86_64` and/or `qemu-system-aarch64`), plus `qemu-img`
- For aarch64 targets: an aarch64 UEFI firmware
  (`AAVMF_CODE.fd`/`AAVMF_VARS.fd`) — aarch64 guests have no BIOS and can only
  boot via UEFI
- cloud-image-utils (for `cloud-localds`)
- curl

On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install qemu-system-x86 qemu-system-arm qemu-efi-aarch64 \
                     qemu-utils cloud-image-utils curl
```

On Fedora/Rocky:
```bash
sudo dnf install qemu-system-x86 qemu-system-aarch64 edk2-aarch64 \
                 qemu-img cloud-utils curl
```

(You only need the packages for the architectures you actually target.)

## Creating an Image

Supported flavors are: `fedora`, `rocky`, `debian`, `ubuntu`.

Supported architectures are: `x86_64` (aka `amd64`) and `aarch64` (aka `arm64`).

### Basic Usage

To create a minimal image without graphics, for the architecture of the host
you are running on:
```bash
./create_vm.sh -f rocky
```

### Choosing the Architecture

`-a` selects the target architecture. It defaults to the architecture of the
host you run the script on, so on an Intel/AMD machine these are equivalent:
```bash
./create_vm.sh -f rocky
./create_vm.sh -f rocky -a x86_64
```

To build an ARM64 image (for an Apple Silicon Mac, an ARM server, a Raspberry
Pi class board, ...):
```bash
./create_vm.sh -f rocky -a aarch64
```

### Cross-Building for the Other Architecture

Building for an architecture other than the host's works, and needs no extra
flags — the script detects the mismatch and switches QEMU from KVM
virtualization to full CPU emulation (TCG) automatically.

Be aware what that costs: emulation is roughly an order of magnitude slower
than a native run, and provisioning compiles EPICS Base and PVXS from source.
A build that takes well under an hour natively can take many hours emulated.
The script prints a warning when it happens.

Whenever you have access to a host of the target architecture, build there
instead.

### Architectures in CI

The GitHub Actions workflows that build images and test roles in QEMU
(`build-cloud-init-images.yml`, `test-roles-*.yml`) need hardware
virtualization, i.e. `/dev/kvm` on the runner:

- **x86_64 runs automatically** on every push and pull request, on
  `ubuntu-latest`, which does provide `/dev/kvm`.
- **aarch64 is opt-in**, because GitHub's hosted arm64 runners
  (`ubuntu-24.04-arm`) offer no nested virtualization and expose no `/dev/kvm`.
  QEMU would silently fall back to emulation and the job would run for hours,
  past GitHub's 6 h job limit — a longer timeout cannot fix that.

To request it anyway (for instance once you have a KVM-capable self-hosted
arm64 runner), start the workflow manually — "Run workflow" offers an
**Architectures** choice of `x86_64`, `aarch64` or `x86_64,aarch64`:
```bash
gh workflow run build-cloud-init-images.yml -f architectures=x86_64,aarch64
```
The choice is turned into the job matrix by the reusable
`.github/workflows/_arch_matrix.yml`, which is where the
architecture → runner/package mapping lives. If a runner turns out to have no
`/dev/kvm`, the job stops early with an explicit error rather than grinding
into a timeout.

The **molecule** role tests (`molecule.yml`) are container-based, need no KVM,
and therefore run on both architectures automatically.

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

To pin provisioning to an exact commit (checked out after cloning the branch), add `-s`:
```bash
./create_vm.sh -f rocky -r https://github.com/myuser/training-vm.git -b my-feature-branch -s <commit-sha>
```

## Output

The resulting images are placed in the `VMs/` directory, named
`<flavor>-<arch>`:
- `VMs/rocky-x86_64.qcow2`: For use with QEMU or other KVM-based hypervisors.
- `VMs/rocky-x86_64.vdi`: For use with VirtualBox.

and correspondingly `VMs/rocky-aarch64.qcow2` / `VMs/rocky-aarch64.vdi` for an
`-a aarch64` build.

Note that an aarch64 guest needs a UEFI-capable hypervisor configuration; when
booting the qcow2 by hand, supply an aarch64 UEFI firmware the same way
`create_vm.sh` does. VirtualBox support for ARM hosts is still preview-quality,
so the VDI is mainly useful for x86_64.

## Troubleshooting

The provisioning happens headlessly. If you need to debug the process, you can
modify `create_vm.sh` to remove the `-nographic` flag from the `"$QEMU_BIN"`
command, which will open a QEMU window where you can watch the console output.

The architecture-dependent part of the QEMU command line (emulator binary,
machine type, CPU model, UEFI firmware) is built by `qemu_setup` in
`cloud-init/qemu_arch.sh`, which is shared with `run_ansible_test.sh`.
