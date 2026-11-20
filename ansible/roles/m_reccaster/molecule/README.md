# Molecule tests for the m_reccaster role

Functional tests: the `default` scenario builds EPICS Base and the recsync
reccaster module in a plain `ubuntu:22.04` container (roles `initial_setup` +
`m_reccaster`, which pulls in `m_base`), then runs the testinfra tests in
`resources/tests/test_reccaster.py`:

| Test | Checks |
|---|---|
| `test_release_dot_local_has_reccaster` | `/opt/epics/RELEASE.local` defines `RECCASTER`, pointing to the `client/` directory of the recsync source tree |
| `test_module_files_are_installed` | `reccaster.dbd`, `reccaster.db` and the `reccaster` libraries (static and shared) are installed |
| `test_demo_ioc_is_not_built` | the recsync demo IOC is left out |
| `test_ioc_accepts_reccaster_iocsh_commands` | as `epics-dev`, an IOC application created with `makeBaseApp.pl` and linked against reccaster builds and accepts `addReccasterEnvVars` and `addReccasterExcludePattern` without complaints |
| `test_caster_waits_for_a_recceiver` | in the same IOC (no recceiver around), `dbgf` shows the `State-Sts` record of `reccaster.db` as `Listening` and `Msg-I` as `Searching` |

The upload of the records to a recceiver and on into ChannelFinder is tested
end to end by the `recceiver` role's scenario.

CI runs the scenario on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/m_reccaster
molecule test
```
