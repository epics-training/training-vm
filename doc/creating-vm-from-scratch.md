# Creating the EPICS Training VM

These instructions describe how to generate the VirtualBox VM
for the EPICS Training from scratch.
The recipe was set up using VirtualBox 7.0.14 on Windows 10,
but it should work similarly on other versions and host systems.

*This will not work for Silicon based Macs. Follow
[these instructions](/doc/creating-vm-from-scratch-apple-silicon.md) for an altnernative.*

## Create the VM

Create a new virtual machine, using the Rocky Linux 9.3 iso image.
(Both a local install from the 10GB DVD iso
or a network install from the 900MB boot iso work.)
Here are the settings we used.
More CPUs and memory always helps -
going lower than these values is not recommended.

![VBox Settings](/doc/training-vm-parameters.png?raw=true "VBox Settings")

You can use the "Server with GUI" or "Workstation" profiles,
no additional software modules are needed.

Create a user (we used epics-dev as the "EPICS Developer")
select "Make this user administrator" (which enables sudo).
We did not set a password, which is fine for a personal VM
that you run on your own computer/laptop.

Consider saving the state in a snapshot, *"9.3 fresh"*.

## Update the system

Become root.
```
$ sudo -i
```

Enable EPEL and update the system.
```
# dnf install -y epel-release && dnf update -y --refresh
```

Reboot (important!).

## Allow passwordless sudo

Become root.

Edit `/etc/sudoers` (by commenting / uncommenting lines)
to allow the `wheel` group to run commands with `NOPASSWORD: ALL`.
This is needed for ansible to run.

## Install dependencies

Install the prerequisites for building the VBox Guest Additions
```
# dnf install -y dkms kernel-devel kernel-headers
```

Reboot.

It is useful to make another snapshot at this point, *"9.3 updated"*.

## Install the VBox Guest Additions

"Insert Guest Additions CD" in the VBox GUI and authorize autostart.

Reboot.

Create a snapshot *"9.3 with Guest Additions <VBox version>"*.

## Get and run the bootstrap script

The remaining steps are done as the regular user.

Copy the script `bootstrap_redhat.sh` onto the VM and run it.
(Preferably from your home directory.)

E.g. (in one audacious step)
```
$ eval "$(curl -L https://raw.githubusercontent.com/epics-training/training-vm/main/bootstrap_redhat.sh)"
```

This will make sure the required software is installed (git, ansible)
and clone this repository with the ansible configuration
into a directory called `bootstrap`.

## Create your local configuration

Inside the `bootstrap/ansible/group_vars` directory,
make a copy of the file `local.yml.sample`, naming it `local.yml`.

Edit `bootstrap/ansible/group_vars/local.yml`
to configure your training VM.

## Run ansible to install the system

```
$ bootstrap/update.sh
```
will install or update the training VM according to your configuration.

The compiling jobs will take their time.
Subsequent runs of the script will not recompile modules unless necessary.
