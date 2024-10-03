# environment parameters
@distro_names = (ENV['VAGRANT_VM_BOX'] || "rocky").split(',')
@cpus = ENV['VAGRANT_VM_CPUS'] || 4
@ansible_args = ENV['VAGRANT_ANSIBLE_ARGS'] || ""

@distros = [
  {
    box: "fedora/40-cloud-base",
    installer: "dnf",
    name: "fedora"
  },
  {
    box: "rockylinux/9",
    installer: "dnf",
    name: "rocky"
  },
  {
    box: "debian/bookworm64",
    installer: "apt",
    name: "debian"
  },
  {
    box: "ubuntu/focal64",
    installer: "apt",
    name: "ubuntu"
  },
]

choices = ["fedora", "rocky", "debian", "ubuntu", "all"]

if not @distro_names.all? { |e| choices.include?(e) }
  print "ERROR: allowed values for VAGRANT_VM_BOX are comma separate distros #{choices} or 'all'"
  exit 1
else
  print "INFO: VAGRANT_VM_BOX is #{@distro_names}"
end