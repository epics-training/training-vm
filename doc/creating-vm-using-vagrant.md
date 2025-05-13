# Create the VM Using Vagrant

Vagrant: making VMs as much fun as containers!

## Introduction

Here are instructions to use Vagrant to build the VirtualBox VM
as an alternative to
[manually creating it from scratch](creating-vm-from-scratch.md).

Advantages:
- The VM is created in a reproducible and fully automated way.
- It's faster because it starts with a pre-built base 'box'.

## Pre-Requisites

Set up the required tools on your host machine:
1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads) (>= 7.1)
2. Install [Vagrant](https://www.vagrantup.com/downloads.html) (>= 2.4.3)
3. Install [git](https://git-scm.com/downloads)

## Initial Installation

Supported Linux distributions are: debian, fedora, rocky, ubuntu.
Make sure you list the distros you require after each vagrant command,
otherwise the default is for the command to apply to all of them.

Before creating a VM,
set the following environment variables as required:

- `VAGRANT_VM_CPUS`:
  number of CPUs to allocate to the VM.
- `VAGRANT_ANSIBLE_ARGS`:
  additional arguments to pass to the ansible-playbook command.

Default CPU count is `VAGRANT_VM_CPUS=4`.
For maximum performance
set CPUS to the number of physical CPUs on a Windows host,
or the number of logical CPUs on a Linux Host (according to giles' tests).

The following example is to bring up the rocky distro.
Change the distro name to the one you want to use
or supply a list of distros separated by spaces.

```bash
# clone this repository
git clone git@github.com:epics-training/training-vm.git
# install the vagrant-vbguest plugin
vagrant plugin install vagrant-vbguest

cd training-vm/vagrant
# start the VM and run the Ansible playbook (adjust CPUS to your host)
VAGRANT_VM_CPUS=16 vagrant up rocky
# install the latest VirtualBox Guest Additions into the VM
vagrant vbguest rocky --auto-reboot
```

In case of kernel updates and a mismatch of VirtualBox versions
between your host and the Vagrant base box image,
the `vagrant vbguest` step fails with not being able
to download the correct version of the kernel development package.
The error messages contain e.g.:

```
Package kernel-devel-5.14.0-427.42.1.el9_4.x86_64 is already installed.
No match for argument: kernel-devel-5.14.0-427.13.1.el9_4.x86_64
```

In that case, reboot the VM from the VirtualBox GUI using 'ACPI shutdown'
and re-run the `vagrant up` and `vagrant vbguest` steps.

Sometimes the `vagrant vbguest` step runs sucessfully,
installs a new version of the Guest Additions,
but does not manage to reboot the VM after that update.

In that case, reboot the VM from the VirtualBox GUI using 'ACPI shutdown'
and re-run the `vagrant up` step.

You can login with username `epics-dev`, no password.

Before publishing an OVA file,
adjust CPUs to a more friendly value for the end user's host machine.

### Adding a CA Certificate

If your institute firewall requires an additional CA certificate,
copy the required certificate (in PEM format)
into the `vagrant` directory (next to the `Vagrantfile`)
and enable the `catrust` role (in the bootstrap step).

## Add the Training Specific Content: Bootstrap and Update

The initial installation is a minimal VM.

The next step in creating your Training-VM instance issue
is to [bootstrap and update the VM](bootstrap-update-vm.md).

Alternatively,
you can add more features by running the Ansible playbook again
after creating a custom local.yml.

- copy the file `ansible/group_vars/everything.yml` to `ansible/group_vars/local.yml`
- edit `ansible/group_vars/local.yml` to enable the features you want
- run `vagrant provision rocky`

## Troubleshooting

If there is a failure in the Ansible steps and you have fixed the issue,
re-run the Ansible playbook
by running `vagrant provision` from outside of the VM
or `vm-setup/update.sh` from inside the VM.

Get rid of one or more of the VMs:
```bash
# all training VMs
vagrant destroy
# or just two distros
vagrant destroy rocky ubuntu
```

You may need to also manually remove a VM's directory
before you can recreate the same VM from scratch.

SSH into the rocky VM:
```
vagrant ssh rocky
```
