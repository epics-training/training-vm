# Available roles

## EPICS Modules

### m_areadetector
The AreaDetector image processing framework
(modules Core, SimDetector and PVADriver)
and their dependency Busy.

### m_base
EPICS Base C++ and PVXS.

### m_opcua
OPC UA Device Support and the open62541 low-level driver.

### m_p4p
Python wrapper for PVAccess (PVXS-based) and PVA Gateway.

### m_pvaPy
Python wrapper for PVAccess (based on the classical PVA stack).

### m_seq
State Notation language compiler and Sequencer.

### m_stream
StreamDevice Device Support.

## Phoebus and Services

### phoebus
Control System Studio / Phoebus.

### archiver_appliance
Minimal install of the EPICS Archiver Appliance.

## Other Clients

### oac_tree
High-level sequencer for automation, operation and control.

## Bluesky Modules

### bluesky
Containerized training setup of Bluesky.

## System Level Roles

### catrust
Enterprise CA certificate install
(needed behind deep packet inspection firewalls).

## Internal Modules
Low-level stuff and dependencies of the above.

### m_asyn
The ASYN Driver framework.

### m_autosave
The AutoSaveRestore (EPICS Process Database persistence) module.

### m_calc
The CALC (array and string calculation) module.

### m_sscan
The SSCAN (multi-dimensional scan record) module.

### docker
Installation of Docker or Podman to run containers.

### initial_setup
One-off role called at the first run in a freshly provisioned VM.

### java
Java SDK needed for Phoebus and Services.

# Adding EPICS modules

m_base provides a task file to install one or more EPICS modules.

## Parameters

- `epics_modules_to_build`: A list of dictionaries, where each dictionary represents an EPICS module to be built.

### Module Configuration Dictionary

Each dictionary in `epics_modules_to_build` should have the following keys:

- `id`: Short name of the module (used for directory naming and internal references).
- `name`: Full name of the module (used in task descriptions).
- `version`: Version string of the module.
- `url`: URL to download the source tarball.
- `release_var`: The variable name to be used in `RELEASE.local` (e.g., `EPICS_BASE`, `ASYN`).
- `release_sortkey`: A two-digit string used to order fragments in `RELEASE.local`.
- `add_to_path`: (Optional) Boolean, if true, the module's `bin` directory will be added to the system `PATH`.
- `required_debs`: (Optional) List of Debian packages required for building.
- `required_rpms`: (Optional) List of RPM packages required for building.
- `enable_repos`: (Optional) List of repositories to enable when installing RPMs.
- `pre_hook`: (Optional) Name of task file to run before the build. Must be in `/tasks/` directory.
- `post_hook`: (Optional) Name of task file to run after the build. Must be in `/tasks/` directory.
- `args`: (Optional) Additional arguments to pass to `make`.
- `exclude`: (Optional) List of patterns to exclude when extracting the tarball.

## Usage Example

In a high-level role `m_example`:

`vars/main.yml`:
```yaml
example_version: "1.0.0"
m_example_modules:
  - id: example
    name: "Example Module"
    version: "{{ example_version }}"
    url: "https://example.com/example-{{ example_version }}.tar.gz"
    release_var: "EXAMPLE"
    release_sortkey: "10"
    pre_hook: "{{ playbook_dir }}/roles/m_example/tasks/example_prep.yml"
```

`tasks/main.yml`:
```yaml
- name: Install Example Module
  include_tasks: {{ epics_build_module_task }}
  vars:
    epics_modules_to_build: "{{ m_example_modules }}"
```
