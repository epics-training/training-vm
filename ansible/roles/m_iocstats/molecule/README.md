# Molecule tests for the m_iocstats role

Functional tests: the `default` scenario builds EPICS Base and iocStats in
a plain `ubuntu:22.04` container (roles `initial_setup` + `m_iocstats`, which
pulls in `m_base`), then runs the testinfra tests in
`resources/tests/test_iocstats.py`:

| Test | Checks |
|---|---|
| `test_release_dot_local_has_iocstats` | `/opt/epics/RELEASE.local` defines `IOCSTATS` |
| `test_module_files_are_installed` | `devIocStats.dbd`, `iocAdminSoft.db` and the `devIocStats` libraries (static and shared) are installed |
| `test_ioc_reports_kernel_version` | as `epics-dev`, an IOC application created with `makeBaseApp.pl` and linked against iocStats builds; running it with `iocAdminSoft.db` loaded, `KERNEL_VERS` (stringin device support) reports `Linux <uname -r>` |
| `test_ioc_reports_process_id` | in the same IOC, `PROCESS_ID` (ai device support) reports a positive PID |

The container's GCC (11) predates the GCC 14 untyped-dset error that the
pre-build hook works around; that is covered on Fedora and recent Ubuntu by
the stage-2 EPICS modules workflow (`.github/workflows/test-roles-modules.yml`).

CI runs the scenario on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/m_iocstats
molecule test
```
