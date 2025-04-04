# Setting Up a Training-VM Instance

The Training-VM is available in four flavours in their stable/current versions:
- rocky: [RockyLinux](https://rockylinux.org/) (compatible to RHEL)
- fedora: [Fedora Linux](https://fedoraproject.org/)
- debian: the "stable" release of [Debian Linux](https://www.debian.org/)
- ubuntu: [Ubuntu Linux](https://ubuntu.com/)

Not all modules are working on all flavours.

Not all modules are working on Mac using Apple Silicon processors.

## Create the Virtual Machine

The first step is to create a VM in the desired flavour.

There are two ways to do that:

1. You can create the VM in the traditional manual way
   by following the
   [instructions for manually creating a Rocky VM](creating-vm-from-scratch.md).
   This is the traditional and slow option.

2. Vagrant can create VirtualBox VMs in a scripted faster fashion,
   based on available base box images.
   Follow the
   [instructions for creating VMs using Vagrant](creating-vm-using-vagrant.md)
   (covering all four flavours).

At this point, you have an "empty" VM
that still needs to get the installation for the specific training event.

If you have a received a link to an "OVA" VM appliance for the empty VM,
you can download and install that appliance
instead of creating the VM in one of the ways described above.

## Bootstrap and Update the Training-VM

Once your VM is up,
you need to install the content
(EPICS, tools, applications, training material and exercises)
for your specific training event.

Pulling together the right versions of the right repositories
is handled by a parent repository called "collection",
which contains the required repos as git submodules.

Each training event has a short name (slug)
that corresponds to a branch in the collection repo.
This setup keeps the versions/repositories for different events
separate and available.
It also allows to get last-minute updates for the event
by updating the collection an re-running the Ansible scripts.

The details are shown in the
[instructions for bootstrapping and updating](bootstrap-update-vm.md).
