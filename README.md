# Powerful Flexible Modular Scripted VM-Setup for EPICS

This Training-VM repo contains code (and documentation)
to set up a virtual machine with EPICS Base and other modules
in a scripted, reproducible fashion.

The original and main use case are EPICS Training events,
where each event uses a different set of training modules.
Nevertheless, the setup can also be used
to prepare a personal development machine
or to prepare portable small instances of "control system"
that can be deployed at collaborators, vendors or customers.

A setup for a specific event can be prepared and updated remotely,
allowing to distribute an "empty" VM
that pulls and installs everything needed for a specific training event
from remote git repos.
(This install process will take some time - depending on host and setup -
typically under an hour.)

To minimize the install time,
a "fully installed" VM can also be distributed,
keeping the possibility to update the content at any time
with last-minute changes.

## VM Options

We are using [VirtualBox](https://www.oracle.com/virtualization/virtualbox/),
which can be run on Linux, Windows and Mac hosts.

The Training-VM is available in four flavours in their stable/current versions:
- rocky: [RockyLinux](https://rockylinux.org/) (compatible to RHEL)
- fedora: [Fedora Linux](https://fedoraproject.org/)
- debian: the "stable" release of [Debian Linux](https://www.debian.org/)
- ubuntu: [Ubuntu Linux](https://ubuntu.com/)

Not all modules are working on all flavours. 

Not all modules are working on Mac using Apple Silicon processors.

## Repository Structure

Everything needed for a specific training event,
the vm setup (this repo) as well as the training modules (slides and examples),
is installed as git submodules of a parent, called the "collection".

The collection repo contains a branch for each training event, named after it.
Any vm instance is configured
by specifying the "slug" (short name) of the training event it is used for.

That branch of the collection contains exactly all modules and configuration
needed for that training event at the right status (commit).

## Workflow

### Create the Virtual Machine

You can create the VM in the traditional manual way.
The `doc` folder contains
[instructions for manually creating a Rocky flavour VM](doc/creating-vm-from-scratch.md).

A much faster way is using [Vagrant](https://www.vagrantup.com/),
which allows for a scripted, automated way to create VirtualBox VMs.
In the same folder you will find
[instructions for creating VMs using Vagrant](doc/vagrant.md)
(covering all four flavours).

### Bootstrap the Training-VM

Once your VM is up, run the script `bootstrap.sh`.
```bash
# from inside the VM
eval "$(curl -L https://raw.githubusercontent.com/epics-training/training-vm/main/bootstrap.sh)"
```

This will ask for the slug of the training event
you want to install the VM for
(i.e., the branch of the collection repo),
download dependencies (git, ansible, ...),
and clone the specified branch of the collection repo.

### Run the `vm-setup/update.sh` Script

This script can be run at any time to pull and install
the latest changes in the setup.

It updates the collection's submodules
and calls Ansible to run the installation procedure.

The Ansible scripts are optimized for execution time
(skipping parts that are already installed and unchanged),
to make the update a light and fast procedure.
