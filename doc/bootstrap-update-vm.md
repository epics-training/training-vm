# Bootstrap and Update the Training-VM

This step installs and updates all training event specific content
on your Training-VM.

## Bootstrap - Run Once on a New VM

Run the script `bootstrap.sh` from inside the VM,
logged in as the `epics-dev` user,
from its home directory.

```bash
eval "$(curl -L https://raw.githubusercontent.com/epics-training/training-vm/main/bootstrap.sh)"
```

This will ask for the slug (shot name) of the training event
you want to install the VM for.
(This maps to a branch of the repo containing the ),
download dependencies (git, ansible, ...),
and clone the specified branch of the collection repo.

Now change into the `training` collection directory.

The file `local.yml` contains the configuration
for your specific training event.
Originally, it has been created
as a copy of the sample file
`vm-setup/ansible/group_vars/local.yml.sample`.

Edit `local.yml` to configure your training VM,
then update your Training-VM.

## Update - Run When Necessary to Update the Setup

The `update.sh` script can be run at any time
to pull and install the latest changes in the setup.
It updates the collection's submodules
and calls Ansible to run the installation procedure.

```bash
vm-setup/update.sh
```

Any additional commandline options
are forwarded to the Ansible call.
E.g., add `-v` one or multiple times to increase verbosity.

The Ansible scripts are optimized for execution time
(skipping parts that are already installed and unchanged),
to make the update a light and fast procedure.

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
This allows to actively maintain different setups
in parallel collection directories.
