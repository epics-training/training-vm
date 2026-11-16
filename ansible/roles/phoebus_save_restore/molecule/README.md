# Molecule tests for the phoebus_save_restore role

Functional tests of the Phoebus save-and-restore service: the `default`
scenario builds Phoebus and sets up Elasticsearch and the save-and-restore
service (roles `initial_setup` + `phoebus` + `phoebus_save_restore`, which
pulls in `elasticsearch`) in an `ubuntu:22.04` container, then runs the
testinfra tests in `resources/tests/test_save_restore.py`.
The container runs systemd as PID 1 (privileged, host cgroup namespace;
image definition shared in `ansible/molecule/systemd/Dockerfile.j2`), so the
role runs with `in_container: false`, exactly as on a VM, and the services
really start.

The end-to-end tests use the REST API the way the Phoebus "Save & Restore"
application does: as the demo user `user` they create a folder and, in it, a
configuration with one PV, then let the service take and save a snapshot.
The PV is a local PV (`loc://molecule_sar_test(42)`) of the service's own PV
pool, so it has a value without an IOC. Node names carry a timestamp, so the
tests can be re-run (`molecule verify`).

| Test | Checks |
|---|---|
| `test_service_is_running_and_enabled` | `elasticsearch` and `save-and-restore` are running and enabled |
| `test_runs_as_unprivileged_user` | the service runs as the `save-and-restore` user |
| `test_epics_settings_reach_the_service` | the service runs with `-Djca.use_env=true` and `-DdefaultProtocol=ca`, and has the `EPICS_*` variables of `save_restore_epics_env` (set in `molecule.yml`) in its environment |
| `test_rest_api_reports_elasticsearch_connected` | the REST API (port 8080, `/save-restore`) answers and reports Elasticsearch as connected |
| `test_phoebus_client_uses_the_service` | `preferences.ini` points the client (`jmasar.service.url`) at the service |
| `test_root_folder_exists` | the root folder of the tree is there |
| `test_changes_need_authentication` | creating a node without credentials is rejected (401) |
| `test_folder_is_listed_under_root` | the new folder is a child of the root folder, owned by `user` |
| `test_configuration_is_stored` | the configuration holds the test PV |
| `test_snapshot_holds_the_pv_value` | the snapshot taken by the service holds the PV's value (42) |
| `test_snapshot_is_found_by_search` | `/search` finds the snapshot by name |
| `test_data_is_stored_in_elasticsearch` | the snapshot data is in the `saveandrestore_snapshot` index |

Building Phoebus makes this one of the slowest scenarios.
CI runs it on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/phoebus_save_restore
molecule test
```
