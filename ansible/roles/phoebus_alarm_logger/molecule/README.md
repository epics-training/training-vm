# Molecule tests for the phoebus_alarm_logger role

Functional tests of the whole Phoebus alarm system: the `default` scenario
builds Phoebus and sets up Kafka, the alarm server, Elasticsearch and the
alarm logger (roles `initial_setup` + `phoebus` + `phoebus_alarm_logger`,
which pulls in `elasticsearch` and `phoebus_alarm` → `kafka`) in an
`ubuntu:22.04` container, then runs the testinfra tests in
`resources/tests/test_alarm_logger.py`.
The container runs systemd as PID 1 (privileged, host cgroup namespace;
image definition shared in `ansible/molecule/systemd/Dockerfile.j2`), so the
role runs with `in_container: false`, exactly as on a VM, and the services
really start.

The end-to-end tests import an alarm configuration (`alarm-server -import`)
with one PV that never connects, so the alarm server raises a
"Disconnected" alarm, and follow it through the system:

| Test | Checks |
|---|---|
| `test_service_is_running_and_enabled` | `kafka`, `elasticsearch`, `alarm-server` and `alarm-logger` are running and enabled |
| `test_alarm_server_created_its_topics` | Kafka has the `Accelerator`, `AcceleratorCommand` and `AcceleratorTalk` topics |
| `test_logger_rest_api_reports_elasticsearch_connected` | the alarm logger's REST API (port 9000) answers and reports Elasticsearch as connected |
| `test_phoebus_client_uses_the_logger` | `preferences.ini` points the Alarm Log (`service_uri`) at the alarm logger |
| `test_exported_config_contains_imported_pv` | `alarm-server -export` returns the imported PV |
| `test_config_change_is_logged_to_elasticsearch` | the configuration message reaches the `accelerator_alarms_config*` index |
| `test_alarm_is_logged_to_elasticsearch` | the alarm (state) message reaches the `accelerator_alarms_state*` index |
| `test_alarm_is_served_by_the_logger_rest_api` | `/search/alarm` on the alarm logger returns the alarm |

Building Phoebus makes this the slowest scenario.
CI runs it on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/phoebus_alarm_logger
molecule test
```
