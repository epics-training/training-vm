#!/bin/bash
# qemu_arch.sh - Shared architecture helpers for create_vm.sh and
# run_ansible_test.sh. Meant to be sourced, not executed.
#
# Provides:
#   normalize_arch <name>            canonical arch name (x86_64 | aarch64)
#   host_arch                        canonical arch of this machine
#   qemu_setup <target_arch> <dir>   sets QEMU_BIN and the QEMU_ARCH_ARGS array
#                                    for booting a <target_arch> guest, using
#                                    <dir> for any writable scratch firmware
#                                    state it needs

# Accept the various spellings people (and distros) use for the same thing.
normalize_arch() {
    case "$1" in
        x86_64|amd64|x64)  echo "x86_64" ;;
        aarch64|arm64)     echo "aarch64" ;;
        *) echo "Unsupported architecture: $1 (supported: x86_64, aarch64)" >&2
           return 1 ;;
    esac
}

host_arch() {
    normalize_arch "$(uname -m)"
}

# Locate an aarch64 UEFI firmware pair (code + writable variable template).
# aarch64 guests have no BIOS - they can only boot via UEFI, so this is
# required, unlike on x86_64 where QEMU's built-in SeaBIOS is enough.
# Echoes "<code_path>:<vars_template_path>".
_find_aarch64_firmware() {
    local pair code vars
    for pair in \
        "/usr/share/AAVMF/AAVMF_CODE.fd:/usr/share/AAVMF/AAVMF_VARS.fd" \
        "/usr/share/edk2/aarch64/QEMU_EFI-silent-pflash.raw:/usr/share/edk2/aarch64/vars-template-pflash.raw" \
        "/usr/share/edk2/aarch64/QEMU_EFI-pflash.raw:/usr/share/edk2/aarch64/vars-template-pflash.raw" \
        "/usr/share/edk2/aarch64/QEMU_CODE.fd:/usr/share/edk2/aarch64/QEMU_VARS.fd" \
        "/usr/share/qemu-efi-aarch64/QEMU_EFI.fd:/usr/share/AAVMF/AAVMF_VARS.fd" \
    ; do
        code=${pair%%:*}
        vars=${pair##*:}
        if [ -f "$code" ] && [ -f "$vars" ]; then
            echo "$pair"
            return 0
        fi
    done

    cat >&2 <<'EOF'
ERROR: No aarch64 UEFI firmware found. aarch64 guests boot via UEFI only.
Install it with one of:
  Debian/Ubuntu: sudo apt-get install qemu-efi-aarch64
  Fedora/Rocky:  sudo dnf install edk2-aarch64
EOF
    return 1
}

# qemu_setup <target_arch> <scratch_dir>
# Sets the globals QEMU_BIN and QEMU_ARCH_ARGS (array).
qemu_setup() {
    local target="$1" scratch="$2" host accel cpu
    host=$(host_arch) || return 1

    if [ "$target" = "$host" ]; then
        # Native: let KVM accelerate, and expose the real CPU to the guest.
        accel="kvm:tcg"
        cpu="host"
        # accel=kvm:tcg silently falls back to emulation when KVM is missing,
        # which turns "native and fast" into "10x slower" with no visible
        # cause - most often a nested-virtualization-less cloud VM. Say so.
        if [ ! -e /dev/kvm ] || [ ! -w /dev/kvm ]; then
            cat >&2 <<EOF
WARNING: /dev/kvm is not available/writable, so this native $target run cannot
         use KVM and QEMU will fall back to emulation (TCG) - roughly an order
         of magnitude slower. Expect build timeouts. Check that hardware
         virtualization is enabled and that you are in the 'kvm' group; note
         that many cloud VMs (including GitHub's arm64 hosted runners) do not
         expose /dev/kvm at all.
EOF
        fi
    else
        # Cross-architecture: KVM can never apply, and -cpu host is invalid
        # without it, so pin plain TCG emulation and the generic max CPU.
        accel="tcg"
        cpu="max"
        cat >&2 <<EOF
WARNING: Building a $target guest on a $host host requires full CPU emulation
         (QEMU TCG). This works, but is roughly an order of magnitude slower
         than a native run - expect the provisioning/build to take many hours.
         Prefer a native $target host where you can.
EOF
    fi

    QEMU_ARCH_ARGS=()
    case "$target" in
        x86_64)
            QEMU_BIN="qemu-system-x86_64"
            QEMU_ARCH_ARGS+=(-M "q35,accel=$accel" -cpu "$cpu")
            ;;
        aarch64)
            QEMU_BIN="qemu-system-aarch64"
            local fw code vars_template vars_copy
            fw=$(_find_aarch64_firmware) || return 1
            code=${fw%%:*}
            vars_template=${fw##*:}
            # The guest needs its own writable copy of the EFI variable store.
            # It is scratch state: the images boot from a pristine template the
            # same way any cloud provider boots them, so nothing that must
            # survive to the next boot is kept here.
            vars_copy="$scratch/efivars.fd"
            cp "$vars_template" "$vars_copy"
            # gic-version=max picks GICv3 where available, lifting the 8-vCPU
            # cap of the default GICv2.
            QEMU_ARCH_ARGS+=(-M "virt,gic-version=max,accel=$accel" -cpu "$cpu")
            # snapshot=off keeps a global -snapshot (used by run_ansible_test.sh
            # to protect the guest disk) from also redirecting the firmware.
            QEMU_ARCH_ARGS+=(-drive "if=pflash,format=raw,unit=0,readonly=on,snapshot=off,file=$code")
            QEMU_ARCH_ARGS+=(-drive "if=pflash,format=raw,unit=1,snapshot=off,file=$vars_copy")
            ;;
        *)
            echo "Unsupported target architecture: $target" >&2
            return 1
            ;;
    esac

    if ! command -v "$QEMU_BIN" >/dev/null; then
        cat >&2 <<EOF
ERROR: $QEMU_BIN not found. Install it with one of:
  Debian/Ubuntu: sudo apt-get install qemu-system-x86 qemu-system-arm qemu-utils
  Fedora/Rocky:  sudo dnf install qemu-system-x86 qemu-system-aarch64 qemu-img
EOF
        return 1
    fi
}
