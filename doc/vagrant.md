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
cd training-vm/vagrant
vagrant up
```

When you reboot the VM it will come up with graphical UI and you can login with username epics-dev.

Finally:
```bash
# from inside the VM
eval "$(curl -L https://raw.githubusercontent.com/epics-training/training-vm/main/bootstrap_redhat.sh)"
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
This will describe how to zero unused blocks and make a small appliance file.