#!/bin/bash
# run_ansible_test.sh - Boot a qcow2 image (built with create_vm.sh -T) and
# run ansible-playbook against the CURRENT checkout's ansible/ tree over SSH,
# logged in as epics-dev (the same user and privilege model - regular user,
# passwordless sudo via ansible's `become` - real bootstrap.sh/update.sh runs
# use). cloud-init is NOT invoked on this boot - it's stage 1's job only.
set -e

CPUS="4"
MEM="6G"
TIMEOUT_MINUTES="60"
SSH_PORT="10022"
IMAGE=""
CONF=""
ARCH=""

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=qemu_arch.sh
source "$SCRIPT_DIR/qemu_arch.sh"

usage() {
    echo "Usage: $0 -i <qcow2 image> -c <conf id> [-a <arch>] [-j <cpus>] [-m <mem>] [-t <timeout minutes>] [-p <ssh port>]"
    echo "  -i: path to the qcow2 image to boot (must be built with create_vm.sh -T;"
    echo "      opened with -snapshot, never modified)"
    echo "  -c: config id, maps to ansible/vars/<id>.yml"
    echo "  -a: architecture of the image: x86_64 (amd64) or aarch64 (arm64)"
    echo "      (default: inferred from the image's -<arch> filename suffix,"
    echo "      else this host's architecture, currently $(host_arch))"
    echo "  -j: number of vCPUs (default: $CPUS)"
    echo "  -m: guest memory (default: $MEM)"
    echo "  -t: timeout in minutes for the ansible-playbook run (default: $TIMEOUT_MINUTES)"
    echo "  -p: host port to forward to the guest's SSH (default: $SSH_PORT)"
    exit 1
}

while getopts "i:c:a:j:m:t:p:" opt; do
    case $opt in
        i) IMAGE=$OPTARG ;;
        c) CONF=$OPTARG ;;
        a) ARCH=$OPTARG ;;
        j) CPUS=$OPTARG ;;
        m) MEM=$OPTARG ;;
        t) TIMEOUT_MINUTES=$OPTARG ;;
        p) SSH_PORT=$OPTARG ;;
        *) usage ;;
    esac
done

[ -z "$IMAGE" ] && usage
[ -z "$CONF" ] && usage
[ -f "$IMAGE" ] || { echo "Image not found: $IMAGE" >&2; exit 1; }

# An explicit -a wins; otherwise trust the <flavor>-<arch>.qcow2 name that
# create_vm.sh produces, and fall back to the host architecture.
if [ -z "$ARCH" ]; then
    case "$(basename "$IMAGE")" in
        *-x86_64.*|*-amd64.*)  ARCH="x86_64" ;;
        *-aarch64.*|*-arm64.*) ARCH="aarch64" ;;
        *) ARCH=$(uname -m) ;;
    esac
fi
ARCH=$(normalize_arch "$ARCH") || exit 1

REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
ANSIBLE_DIR="$REPO_ROOT/ansible"
[ -f "$ANSIBLE_DIR/vars/${CONF}.yml" ] || { echo "No such config: ansible/vars/${CONF}.yml" >&2; exit 1; }

SSH_KEY="$SCRIPT_DIR/ci_test_key"
chmod 600 "$SSH_KEY"

WORK_DIR=$(mktemp -d)
cleanup() {
    [ -n "${QEMU_PID:-}" ] && kill "$QEMU_PID" 2>/dev/null
    [ -n "${QEMU_PID:-}" ] && wait "$QEMU_PID" 2>/dev/null
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT

# Common to both ssh and scp - NOT including the port flag, since ssh uses
# -p and scp uses -P for it.
SSH_KEY_OPTS=(-i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
              -o LogLevel=ERROR -o BatchMode=yes -o ConnectTimeout=5)
SSH_OPTS=(-p "$SSH_PORT" "${SSH_KEY_OPTS[@]}")

# Pick the emulator, machine type, CPU model and (on aarch64) UEFI firmware
# that match the image's architecture.
qemu_setup "$ARCH" "$WORK_DIR"

echo "Booting QEMU (snapshot mode, no cloud-init) with image=$IMAGE arch=$ARCH conf=$CONF ..."
"$QEMU_BIN" \
    "${QEMU_ARCH_ARGS[@]}" \
    -m "$MEM" \
    -smp "$CPUS" \
    -no-reboot \
    -snapshot \
    -drive file="$IMAGE",if=virtio \
    -display none \
    -serial file:"$WORK_DIR/console.log" \
    -monitor none \
    -net nic,model=virtio -net user,hostfwd=tcp::"$SSH_PORT"-:22 &
QEMU_PID=$!

echo "Waiting for SSH on port $SSH_PORT..."
ssh_ready=false
for _ in $(seq 1 90); do
    if ! kill -0 "$QEMU_PID" 2>/dev/null; then
        echo "ERROR: qemu exited before SSH became available." >&2
        break
    fi
    if ssh "${SSH_OPTS[@]}" epics-dev@localhost true 2>/dev/null; then
        ssh_ready=true
        break
    fi
    sleep 5
done

if [ "$ssh_ready" != true ]; then
    echo "ERROR: SSH to the guest never became available. Console log follows:" >&2
    cat "$WORK_DIR/console.log" >&2
    exit 124
fi

echo "Copying ansible/ into guest..."
scp -q -r -P "$SSH_PORT" "${SSH_KEY_OPTS[@]}" "$ANSIBLE_DIR" epics-dev@localhost:/home/epics-dev/ansible-src

echo "Running ansible-playbook (${CONF}) in guest..."
set +e
timeout -k 60s "${TIMEOUT_MINUTES}m" \
    ssh "${SSH_OPTS[@]}" epics-dev@localhost \
    "cd /home/epics-dev/ansible-src && ansible-galaxy install -r requirements.yml >/home/epics-dev/galaxy.log 2>&1; ansible-playbook -v playbook.yml -e '@vars/${CONF}.yml'"
ANSIBLE_STATUS=$?
set -e

if [ "$ANSIBLE_STATUS" -eq 124 ]; then
    echo "ERROR: ansible-playbook run exceeded ${TIMEOUT_MINUTES}m timeout" >&2
fi

exit "$ANSIBLE_STATUS"
