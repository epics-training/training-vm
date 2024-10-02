# environment parameters
@distro_name = ENV['VAGRANT_VM_BOX'] || "rocky"
@cpus = ENV['VAGRANT_VM_CPUS'] || 4
@ansible_args = ENV['VAGRANT_ANSIBLE_ARGS'] || ""

@distros = [
  {
    box: "fedora/40-cloud-base",
    installer: "dnf",
    ip: "192.168.100.10",
    name: "fedora"
  },
  {
    box: "rockylinux/9",
    installer: "dnf",
    ip: "192.168.100.11",
    name: "rocky"
  },
  {
    box: "debian/bookworm64",
    installer: "apt",
    ip: "192.168.100.12",
    name: "debian"
  },
  {
    box: "ubuntu/focal64",
    installer: "apt",
    ip: "192.168.100.13",
    name: "ubuntu"
  },
]

choices = ["fedora", "rocky", "debian", "ubuntu", "all"]

if not choices.include?(@distro_name)
  print "ERROR: allowed values for VAGRANT_VM_BOX are #{choices}"
  exit 1
end