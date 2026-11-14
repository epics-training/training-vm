# Molecule tests for the archiver_appliance role

Functional tests: the `default` scenario needs real services (MariaDB,
Tomcat), so it runs a privileged systemd container (`ubuntu:22.04` plus
systemd, see `resources/Dockerfile.j2`) with `in_container: false`. It
converges the roles `initial_setup`, `m_base` (IOC and `pvget` for the
tests), `phoebus` (Data Browser preferences) and `archiver_appliance`, then
runs the testinfra tests in `resources/tests/test_archiver_appliance.py`.

Tests marked *IOC* use a temporary IOC (`softIocPVA`) that serves two
counter PVs. The appliance archives one over PV Access (its default) and
the other over Channel Access (`ca://` prefix). Tests that are parametrized
over both PVs run once for each protocol.

| Test | Checks |
|---|---|
| `test_tomcat_version` | Tomcat's `RELEASE-NOTES` match `tomcat_version` from the role defaults |
| `test_appliance_version` | `getApplianceInfo` reports `archiver_appliance_version` from the role defaults |
| `test_all_components_are_deployed_with_the_same_version` | `getVersions`: engine, etl and retrieval answer with the same version as mgmt |
| `test_database_tables_exist` | the `archappl` MariaDB database has the appliance's tables |
| `test_databrowser_uses_local_archiver` | the Data Browser's default archive in `preferences.ini` is `pbraw://localhost:17665/retrieval` |
| `test_service_is_running_and_enabled` | the `mariadb` and `archiver-appliance` services are running and enabled |
| `test_appliance_is_running` | `getApplianceInfo` answers for `appliance0` |
| `test_management_ui_is_served` | the management UI (the Training-VM homepage link) is served |
| `test_pv_is_archived_over_requested_protocol` *IOC* | each PV is archived (`getPVStatus`), over the requested protocol (`usePVAccess` in `getPVTypeInfo`) |
| `test_archived_pvs_are_stored_in_database` *IOC* | the PVs' configuration is in the `PVTypeInfo` table |
| `test_samples_are_written_to_short_term_store` *IOC* | the engine writes `.pb` files for each PV into `storage/sts` |
| `test_databrowser_can_fetch_archived_samples` *IOC* | the Data Browser's archive URL delivers samples of each PV (`getData.json`) |
| `test_databrowser_can_fetch_raw_data` *IOC* | ...also in the pbraw format the Data Browser requests (`getData.raw`) |
| `test_archiving_survives_restart` *IOC* | after restarting the `archiver-appliance` service, both PVs are archived again and new samples arrive |

The tests run in file order. The restart test has to come last, because
stopping the appliance moves the short term store into the medium term
store.

CI runs the scenario on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/archiver_appliance
molecule test
```
