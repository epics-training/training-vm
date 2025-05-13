# environment parameters

# !! Make sure the CI settings (in .../.github/test_docker.sh) are equivalent

@cpus = ENV['VAGRANT_VM_CPUS'] || 4
@ansible_args = ENV['VAGRANT_ANSIBLE_ARGS'] || ""

@distros = [
  {
    box: "fedora/41-cloud-base",
    installer: "dnf",
    name: "fedora"
  },
  {
    box: "bento/rockylinux-9",
    installer: "dnf",
    name: "rocky"
  },
  {
    box: "debian/bookworm64",
    installer: "apt",
    name: "debian"
  },
  {
    box: "bento/ubuntu-24.04",
    installer: "apt",
    name: "ubuntu"
  },
]
