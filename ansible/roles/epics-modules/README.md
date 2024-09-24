# epics-modules role

EPICS Support modules follow a common structure
and can be built using a standard procedure.

The epics-modules role is a generic role
that installs an arbitrary number of such EPICS modules.

## Selection of modules to build

In the user's `local.yml`, a simple list `epics_modules_list`
defines which modules are built and their build order.

Building the module `base` is mandatory,
as it contains the EPICS build system, which is needed to compile any module.

## Configuration of supported modules

The supported modules are defined in `epics-modules/vars/main.yml`
as a dictionary `epics_modules` of modules
and module-specific parameters.

| Parameter       | Comments |
| --------------- | -------- |
| name            | Name that is used in task logs. |
| version         | Version number. |
| url             | Download URL for the source tar |
| release_var     | Variable name to use in the RELEASE file. |
| release_sortkey | Sort order of RELEASE entries. |
| add_to_path     | Whether to append the bin directory to teh user's PATH variable. |
| required_debs   | List of DEB names of dependencies that need to be installed before the build for Debian distros. |
| required_rpms   | List of RPM names of dependencies that need to be installed before the build for RedHat distros. |
| enable_repos    | List of additional repositories to enable when installing the required RPMs. |
| pre_hook        | Playbook to run before building the module. |
| post_hook       | Playbook to run after building the module. |
