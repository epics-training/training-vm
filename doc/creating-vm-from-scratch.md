# Creating the EPICS Training VM

TODO - requires rework for multi-distro

These instructions describe how to generate the VirtualBox VM
for the EPICS Training from scratch.
The recipe was set up using VirtualBox 7.0.14 on Windows 10,
but it should work similarly on other versions and host systems.

VirtualBox >=7.1 now supports Apple Silicon based Macs.
The recipe below has also been tested with VirtualBox 7.1.6
and an Apple Silicon M2 MacBook using Rocky Linux 9.5.
The instructions generally work,
but be aware of issues #12 and #13 for the actual EPICS training setup.

## Create the VM

Create a new virtual machine, using an Rocky Linux (>= 9.4) iso image.
(Both a local install from the 10GB DVD iso
or a network install from the 900MB boot iso work.)
Here are the settings we used.
More CPUs and memory always helps -
going lower than these values is not recommended.

![VBox Settings](/doc/training-vm-parameters.png?raw=true "VBox Settings")

You can use the "Server with GUI" or "Workstation" profiles,
no additional software modules are needed.

Create a user (we used epics-dev as the "EPICS Developer")
and select "Make this user administrator" (which enables sudo).
We did not set a password, which is fine for a personal VM
that you run on your own computer/laptop.

Consider saving the state in a snapshot, *"rocky fresh"*.

## Update the system

Become root.
```
$ sudo -i
```

Enable EPEL and update the system.
```
# dnf install -y epel-release && dnf update -y --refresh
```

**Reboot (important!).**

Note: If you're working with an older snapshot
and this command produces unexpected weird errors
("SSL verification error: certificate is not yet valid" or similar),
make sure your system time is updated.
(E.g., flip the "auto/manual" switch in the system setting back and forth.)

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

**Reboot.**

It is useful to make another snapshot at this point, *"rocky updated"*.

## Install the VBox Guest Additions

"Insert Guest Additions CD" in the VBox GUI and authorize autostart.

**Reboot.**

In the `Devices` menu of VBox GUI you can now switch on "Shared Clipboards",
and setup "Shared Folders".

If you encounter `Permission denied` issues with mounted folders,
you can try running (might require relog or reboot):

```
sudo usermod -aG vboxsf $(whoami)
```

Note: If you're experiencing unexpected graphics issues
(e.g., diagonal patterns that change with mouse actions),
try enabling or disabling 3D acceleration in the VM settings.

Create a snapshot *"rocky with Guest Additions <VBox version>"*.

## Get and run the bootstrap script

Install git:

```
sudo dnf install -y git
```

The remaining steps are done as the regular user.

Copy the script `bootstrap.sh` onto the VM and run it.
(Preferably from your home directory.)

E.g. (in one audacious step)
```
$ eval "$(curl -L https://raw.githubusercontent.com/epics-training/training-vm/main/bootstrap.sh)"
```

This will first make sure the required software is installed (git, ansible).
Then it will clone this repository with the ansible configuration
into a directory called `training`.

## Create your local configuration

Change into the `training` directory.

The file `local.yml` has been created as a copy
of the sample file `vm-setup/ansible/group_vars/local.yml.sample`.

Edit `local.yml` to configure your training VM.

## Run ansible to install the system

*For Apple Silicon users: Be aware of issues #12 and #13 before running ansible*

```
$ vm-setup/update.sh
```
will install or update the training VM according to your configuration.

The compiling jobs will take their time.
Subsequent runs of the script will not recompile modules unless necessary.
