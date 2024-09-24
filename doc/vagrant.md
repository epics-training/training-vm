# Vagrant VM Creation

vagrant: making VMs as much fun as containers!

## Introduction

Here are instructions to use vagrant to build the Virtualbox VM as an alternative to [creating-vm-from-scratch.md](creating-vm-from-scratch.md).

Advantages:
- The VM is created in a reproducible and fully automated way.
- Its faster because it starts with a pre-built rocky9 base box.


## Pre-requisites

Setup the required tools on your host machine:
1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
   - WARNING: VirtualBox 7.1 is not compatible with Vagrant 2.4.1, use VirtualBox 7.0 until Vagrant 2.4.2 is released.
1. Install [Vagrant](https://www.vagrantup.com/downloads.html)
1. Install [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/installation_distros.html)
1. Install [git](https://git-scm.com/downloads)

## Steps

```bash
git clone git@github.com:epics-training/training-vm.git
vagrant plugin install vagrant-vbguest
cd training-vm/vagrant
# start the VM and run the ansible playbook (adjust CPUS to your host)
VAGRANT_VM_CPUS=14 VAGRANT_VM_BOX=debian vagrant up
# OR
VAGRANT_VM_CPUS=14 VAGRANT_VM_BOX=fedora vagrant up
# add in the guest additions and reboot to launch the graphical UI
vagrant vbguest --auto-reboot
```
vbguest step may wait indefinitely for the VM to reboot. If it does, you can manually reboot the VM from the VirtualBox GUI using ACPI shutdown.

You can login with username epics-dev, no password.

Before publishing an OVA file, adjust CPUs to a more friendly value for the end user's host machines.

Finally:
```bash
# from inside the VM
eval "$(curl -L https://raw.githubusercontent.com/epics-training/training-vm/main/bootstrap.sh)"
```
see [creating-vm-from-scratch.md](creating-vm-from-scratch.md) for details regarding the bootstrap script.

## Troubleshooting

If there is a failure in the ansible steps and you have fixed the issue, re-run the ansible playbook by running `vagrant provision`.

Get rid of the VM by running
```
vagrant destroy
```

## Skrinking the VM into a small appliance file

TODO
This will describe how to zero unused blocks and make a smaller appliance file.