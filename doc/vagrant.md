# Vagrant VM Creation

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
1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
   - WARNING: VirtualBox 7.1 is not compatible with Vagrant 2.4.1 or 2.4.2,
     use VirtualBox 7.0 until Vagrant 2.4.3 is released.
2. Install [Vagrant](https://www.vagrantup.com/downloads.html)
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
adjust CPUs to a more friendly value for the end user's host machine
and shrink the disk image (see below).

## Adding More Features

The initial installation is a minimal VM. 
You can add more features by running the Ansible playbook again
after creating a custom local.yml.

- copy the file `ansible/group_vars/everything.yml` to `ansible/group_vars/local.yml`
- edit `ansible/group_vars/local.yml` to enable the features you want
- run `vagrant provision rocky`

Alternatively, you can do this from inside the VM:

```bash
# from inside the VM
eval "$(curl -L https://raw.githubusercontent.com/epics-training/training-vm/main/bootstrap.sh)"
```

The above step clones the training-vm repository
and additional training material into the VM.

Now change into the `training` directory.

The file `local.yml` has been created as a copy
of the sample file `vm-setup/ansible/group_vars/local.yml.sample`.

Edit `local.yml` to configure your training VM,
then re-run the Ansible playbook:

```
$ vm-setup/update.sh
```

## Extended Configuration Options

To support development,
the behaviour of the `bootstrap.sh` script can be adapted
using a bootstrap setup file that is sourced by the script.

Create a file using the default name `~/bootstrap_setup`
that contains settings in bash syntax.

- `COLLECTION`: name of the directory for clone the collection into
  (default `training`)
- `COLLECTION_REPO`: URL of the repo to clone for the collection
  (default: `https://github.com/epics-training/training-collection`)
- `SLUGFILE`: file to store the slug (branch) name
  (default: `/etc/epics-training`)

You can redirect any of the submodules
to be directly cloned from a different location.
E.g., to clone the `vm-setup` submodule
from johndoe's fork of the `training-vm` repo (`test-feature` branch):
```
REPO[vm-setup]=https://github.com/johndoe/training-vm
BRANCH[vm-setup]=test-feature
```

The `bootstrap.sh` script
can take the name of a bootstrap setup file as parameter.
This allows to have different setups in parallel collection directories.

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

## Shrinking the VM into a Small Appliance File

TODO
This will describe how to zero unused blocks and make a smaller appliance file.