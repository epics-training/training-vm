# Creating the EPICS Training VM for Apple Silicon

TODO - requires rework for Debian

These instructions explain how to set up the EPICS training VM
on Apple Silicon Mac.
Differing from the normal VM,
this version is based on the `aarch64` architecture.

As VirtualBox does not support Apple Silicon based Macs yet,
you will have to use [UTM](https://github.com/utmapp/UTM).
You can download it for free from Github or buy it via the AppStore.

The recipe was set up using UTM 4.4.5
on a Macbook Air M2 using MacOS 14.1.1,
but it should work similarly on other versions.

In general this follows the instructions for the general VM
as much as possible.

## Create the VM

Once you installed [UTM](https://github.com/utmapp/UTM),
create a new virtual machine.
This will require the `arm64 / aarch64` version
of [Rocky Linux 9](https://rockylinux.org/download/).
It was tested to work with the boot image,
but other images probably work, too.

It was also tested with Ubuntu, but the below instructions follow the installation
using Rocky Linux / RPM package manager.

Follow these steps:

1. Create VM
2. Choose Virtualization
3. Choose Linux
4. (Optional) Choose Apple Virtualization
5. Select the Rocky Linux aarch64 image
6. Set at least 4096 MB of RAM and two cores
7. Set the space size to at least 20 GB
8. Continue
9. Set a name for the VM and save.

More CPUs and memory always helps -
going lower than these values is not recommended.

In regard to the virtualization option
between Apple and QEMU: Both work.
Apple virtualization provides better adjustment to screen resolution
and seems more responsive.

## Set up Linux

Once you start the VM,
select the direct install option.
This will take a while,
where the VM seems unresponsive.

You can use the "Server with GUI" or "Workstation" profiles,
no additional software modules are needed.

Create a user (we used epics-dev as the "EPICS Developer")
and select "Make this user administrator" (which enables sudo).
We did not set a password, which is fine for a personal VM
that you run on your own computer/laptop.

## Installation

Depending on the options you chose,
the installation will take some time.
Once it is finished and you restart the VM,
the freshly installed Linux system should boot.

*For currently unknown reasons
you might end up with a VM which does not boot into the installed Linux,
but will still only allow to boot into the provided installtion image.
See the discussion in
[PR #14](https://github.com/epics-training/training-vm/pull/14)
for more details.*

## Update the system

Become root and enable EPEL and update the system.

```bash
sudo -i
dnf install -y epel-release && dnf update -y --refresh
```

Reboot (important!).

## Allow passwordless sudo

Become root.

Edit `/etc/sudoers`
to allow the `wheel` group to run commands with `NOPASSWORD: ALL`.
This is needed for ansible to run. It should look something like this:

```
## Same thing without a password
%wheel	ALL=(ALL)	NOPASSWD: ALL
```

## Get and run the bootstrap script

The remaining steps are done as the regular user.

Copy the script `bootstrap_redhat.sh` onto the VM and run it.
(Preferably from your home directory.)

E.g. (in one audacious step)

```bash
eval "$(curl -L https://raw.githubusercontent.com/epics-training/training-vm/main/bootstrap_redhat.sh)"
```

This will make sure the required software is installed (git, ansible)
and clone this repository with the ansible configuration
into a directory called `training`.

## Create your local configuration

Inside the `training/vm-setup/bootstrap/ansible/group_vars` directory,
make a copy of the file `local.yml.sample`, naming it `local.yml`.
Edit this file according to the features and systems
you want to prepare for the VM.

### Configure constraints due to arm architecture

While most systems, including EPICS Base and modules,
just work with the `aarch64` architecture,
there are some issues related to Python modules which are used.

You will need to follow the workarounds listed in the issue descriptions:

- Do not activate Bluesky module
  (see issue [#12](https://github.com/epics-training/training-vm/issues/12))
- Switch off building documention for Phoebus
  (see issue [#13](https://github.com/epics-training/training-vm/issues/13))

## Run ansible to install the system

Navigate to your `training` repository and run `vm-setup/update.sh`:

```bash
cd training
./vm-setup/update.sh
```

This will install or update the training VM according to your configuration.

The compiling jobs will take their time.
Subsequent runs of the script will not recompile modules unless necessary.
