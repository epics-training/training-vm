## Configuration Setups

This folder contains collections of configurations and user setups.

*File: `vars/ci-*.yml`*

Setups for the different role-testing CI runs used on GitHub Actions.
Each is applied against a pre-built qcow2 VM image (from
`.github/workflows/build-cloud-init-images.yml`) that already has EPICS
Base installed, so these overrides only need to add the roles/modules
specific to that test group.

*File: `vars/container.yml`*

Small setup for running inside containers.

*File: `vars/everything.yml`*

Full setup that tries to install as many roles/modules as possible.
Does not work inside containers.

*File: `vars/local.yml`*

Reasonably small setup.

*File: `vars/local.yml.sample`*

Commented sample of a setup file.
Copy the content to `local.yml` or a new setup file
and change the content as required.

---

## Differences Between Architectures

Both `x86_64` and `aarch64` are supported, as build host and as target.
Roles get their architecture-dependent names from the `arch` variable
(see [`roles/README.md`](../roles/README.md)); the differences that are not
just naming are:

- `m_opcua`: the UaExpert client is a closed-source binary that Unified
  Automation only ships for x86_64 Linux, so it is not installed on `aarch64`.
  The module itself builds; only the interactive OPC UA browsing exercise is
  unavailable.
- `oac_tree`: on RedHat-family distros the Raven repository (which exists
  solely to provide the cosmetic `adwaita-qt6` Qt style) has no `aarch64` tree,
  so both are skipped there. oac-tree builds and runs, using the default Qt6
  style.

## Differences Between Flavors

Rocky is the only flavor that builds everything.

Ubuntu builds everything except `pvaPy`.

- `bluesky` cannot build in CI because that would need containers inside containers.
  (There are ways to do that, though.)
- EPICS module `pvaPy` - downgrading to 5.3.1 makes it build on Rocky.
  The later versions try to check for boost 1.78.0 and fail.
  5.3.1 won't build on distros with Python 3.12.
  5.3.1 also fails on Ubuntu for different boost version reasons.
- `areaDetector` uses a deprecated function in `xmllib2`;
  Fedora's version is too new.
- `areaDetector` also fails on debian because its version of ansible does not support 'search_string' in lineinfile which is used in adcore_prep.yml. Trying to get an new ansible from the ubuntu ppa (as per ansible docs) fails with dependecy conflicts.
