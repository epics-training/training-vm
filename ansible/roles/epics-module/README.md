# epics-module role

Internal generic role to install one or more EPICS modules.

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

In a high-level role `m-example`:

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
    pre_hook: "{{ playbook_dir }}/roles/m-example/tasks/example_prep.yml"
```

`tasks/main.yml`:
```yaml
- name: Install Example Module
  include_role:
    name: epics-module
  vars:
    epics_modules_to_build: "{{ m_example_modules }}"
```
