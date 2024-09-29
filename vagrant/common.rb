
distro_name = ENV['VAGRANT_VM_BOX'] || "debian"

distros = {
  'fedora': {
    box: "fedora/40-cloud-base",
    installer: "dnf",
  },
  'rocky': {
    box: "rockylinux/9",
    installer: "dnf",
  },
  'debian': {
    box: "debian/bookworm64",
    installer: "apt",
  },
  'ubuntu': {
    box: "ubuntu/focal64",
    installer: "apt",
  },
}

if not distros.key?(distro_name.to_sym)
  print "Unknown distro: #{distro_name}, supported distros: #{distros.keys}\n"
  exit 1
end

@distro = distros[distro_name.to_sym]
@cpus = ENV['VAGRANT_VM_CPUS'] || 4

