# Vagrant VM Creation

vagrant: making VMs as much fun as containers!

## Introduction

Here are instructions to use vagrant to build the Virtualbox VM as an alternative to [creating-vm-from-scratch.md](creating-vm-from-scratch.md).

Advantages:
- The VM is created in a reproducible and fully automated way.
- Its faster because it starts with a pre-built base 'box'.

## Pre-requisites

Setup the required tools on your host machine:
1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
   - WARNING: VirtualBox 7.1 is not compatible with Vagrant 2.4.1 or 2.4.2, use VirtualBox 7.0 until Vagrant 2.4.3 is released.
1. Install [Vagrant](https://www.vagrantup.com/downloads.html)
1. Install [git](https://git-scm.com/downloads)

## Initial Installation

Supported distributions are: debian, fedora, rocky, ubuntu. Make sure you list the distros you require after each vagrant command, otherwise the default is for the command to apply to all of them.

Before creating a VM set the following environment variables as required:

- `VAGRANT_VM_CPUS`: to the number of CPUS to allocate to the VM.
- `VAGRANT_ANSIBLE_ARGS`: additional arguments to pass to the anisble-playbook command.

Default cpus count is `VAGRANT_VM_CPUS=4`. For maximum performance set CPUS to the number of physical CPUS on a Windows host, or the number of logical CPUS on a Linux Host (according to giles tests).

The following example is to bring up the rocky distro. Change the distro name to the one you want to use or supply a list of distros separated by spaces.
```bash
# clone this repository
git clone git@github.com:epics-training/training-vm.git
# install the vagrant-vbguest plugin
vagrant plugin install vagrant-vbguest

cd training-vm/vagrant rocky
# start the VM and run the ansible playbook (adjust CPUS to your host)
VAGRANT_VM_CPUS=16 vagrant up rocky
# install the latest VirtualBox Guest Additions into the VM
vagrant vbguest rocky --auto-reboot
```

The last vbguest step may wait indefinitely for the VM to reboot. If it does, you can manually reboot the VM from the VirtualBox GUI using ACPI shutdown.

You can login with username epics-dev, no password.

Before publishing an OVA file, adjust CPUs to a more friendly value for the end user's host machines.

## Add more features

The initial installation is a minimal VM. You can add more features by running the ansible playbook again after creating a custom local.yml.

- copy the file `ansible/group_vars/everything.yml` to `ansible/group_vars/local.yml`
- edit `ansible/group_vars/local.yml` to enable the features you want
- run `vagrant provision rocky`

Alternatively you can do this from inside the VM as follows:

```bash
# from inside the VM
eval "$(curl -L https://raw.githubusercontent.com/epics-training/training-vm/main/bootstrap.sh)"
```

The above clones the training-vm repository and additional training material into the VM.

Now change into the `training` directory.

The file `local.yml` has been created as a copy
of the sample file `vm-setup/ansible/group_vars/local.yml.sample`.

Edit `local.yml` to configure your training VM and re-run the ansible playbook as follows:

```
$ vm-setup/update.sh
```

## Troubleshooting

If there is a failure in the ansible steps and you have fixed the issue, re-run the ansible playbook by running `vagrant provision` from outside of the VM or `vm-setup/update.sh` from inside the VM.

Get rid of one or more of the VMs:
```bash
# all training VMs
vagrant destroy
# or just two distros
vagrant destroy rocky ubuntu
```

SSH into the rocky VM:
```
vagrant ssh rocky
```

## Shrinking the VM into a small appliance file

TODO
This will describe how to zero unused blocks and make a smaller appliance file.