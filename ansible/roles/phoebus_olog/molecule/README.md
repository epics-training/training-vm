# Molecule tests for the phoebus_olog role

Functional tests of the Olog service: the `default` scenario builds Olog
and sets up Elasticsearch and MongoDB (role `phoebus_olog`, which pulls in
`java`, `elasticsearch` and `mongodb`) in an `ubuntu:22.04` container, then
runs the testinfra tests in `resources/tests/test_olog.py`.
The container runs systemd as PID 1 (privileged, host cgroup namespace;
image definition shared in `ansible/molecule/systemd/Dockerfile.j2`), so the
role runs with `in_container: false`, exactly as on a VM, and the services
really start.

The end-to-end tests create a log entry with an attachment through the REST
API (as the Phoebus client does) and read both back:

| Test | Checks |
|---|---|
| `test_service_is_running_and_enabled` | `elasticsearch`, `mongodb` and `olog` are running and enabled |
| `test_runs_as_unprivileged_user` | the JVM runs as the `olog` user |
| `test_service_info_reports_backends_connected` | `GET /Olog` reports version 6.x, Elasticsearch connected (cluster `training-vm`) and the MongoDB server |
| `test_https_port_answers` | the HTTPS port (4181, self-signed certificate) answers |
| `test_default_logbooks_created` | the default logbooks `operations` and `controls` exist |
| `test_authentication_required_for_writes` | creating a log entry without credentials is refused (401) |
| `test_built_in_accounts_can_log_in` | `user`/`userPass` and `admin`/`adminPass` can log in |
| `test_log_entry_is_stored_and_searchable` | the log entry can be read back and found by a text search (Elasticsearch) |
| `test_attachment_is_stored_in_mongodb` | the attachment can be read back (MongoDB GridFS) |
| `test_cors_allows_the_web_client` | a CORS preflight from the web client's origin is allowed |

CI runs the scenario on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/phoebus_olog
molecule test
```
