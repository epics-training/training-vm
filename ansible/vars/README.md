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
