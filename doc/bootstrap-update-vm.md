# Bootstrap and Update the Training-VM

This step installs and updates all training event specific content
on your Training-VM. This assumes you have set up your VM
following the [instructions](instructions).

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

*Apple Silicon users: Be aware of issues #12 and #13 before running ansible*

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

- `COLLECTION`: name of the local directory
   to clone the training collection into
  (default `training`)
- `COLLECTION_REPO`: URL of the repo to clone the collection from
  (default: `https://github.com/epics-training/training-collection`)
- `SLUGFILE`: file to store the slug (branch) name
  (default: `/etc/epics-training`)

The `COLLECTION_REPO` setting can be used
to point to a fork of the base setup.
This may be useful for developing and testing changes
to the `bootstrap.sh` or `update.sh` scripts.

If you want to develop or test a different version
of a specific training submodule,
you can do that using the `REPO[<submodule>]=<url>` syntax.
This example directly clones the `vm-setup` submodule
from johndoe's fork of the `training-vm` repo (`test-feature` branch)
instead of using the git submodule specified in the collection:
ranch):
```
REPO[vm-setup]=https://github.com/johndoe/training-vm
BRANCH[vm-setup]=test-feature
```
The list of available submodules shows up
at the top level of the collection repo
(on your event-specific branch defined by the slug).

The `bootstrap.sh` script
can take the name of a bootstrap setup file as parameter.
This allows to actively maintain different independent setups
in parallel collection directories.
