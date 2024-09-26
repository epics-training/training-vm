
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

@distro = distros[distro_name.to_sym]
@box = @distro[:box]
@cpus = ENV['VAGRANT_VM_CPUS'] || 4

installer = @distro[:installer]
args = ENV['VAGRANT_VM_ARGS'] || ""

@install_script = "
      if [ '"+ installer +"' == 'apt' ]; then
        add-apt-repository ppa:ansible/ansible; apt-get update
        apt-get install -y ansible python3-jmespath
      elif [ '"+ installer +"' == 'dnf' ]; then
        dnf install -y epel-release && dnf update -y --refresh
        dnf install -y ansible python3-jmespath
      fi

      ansible-galaxy install -r /ansible/requirements.yml || true
      ansible-playbook -i /ansible/hosts -e initial_setup=true /ansible/playbook.yml "+ args