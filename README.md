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

## Technology

We are using [VirtualBox](https://www.oracle.com/virtualization/virtualbox/)
to create the virtual machine,
which can be run on Linux, Windows and Mac hosts.

We are using [Ansible](https://docs.ansible.com/)
to install and configure the software on the Training-VM.

## Workflow

There are two steps to create a Training-VM instance:

1. Create the VirtualBox VM
   ([manually](doc/creating-vm-from-scratch.md) or
   [using Vagrant](doc/creating-vm-using-vagrant))
2. [Bootstrap/Update](doc/bootstrap-update-vm.md) the Training-VM
   to install the training-specific software and content

Follow the [instructions](doc/instructions.md)
to learn how to set up your VM instance.
If you already have set up your VM,
you can directly jump to the
[bootstrap and update section](doc/bootstrap-update-vm).