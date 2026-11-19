# Molecule tests for the mongodb role

Functional tests: the `default` scenario installs MongoDB (role `mongodb`)
in an `ubuntu:22.04` container, then runs the testinfra tests in
`resources/tests/test_mongodb.py`.
The container runs systemd as PID 1 (privileged, host cgroup namespace;
image definition shared in `ansible/molecule/systemd/Dockerfile.j2`), so the
role runs with `in_container: false`, exactly as on a VM, and the service
really starts.

| Test | Checks |
|---|---|
| `test_service_is_running_and_enabled` | the `mongodb` systemd service is running and enabled |
| `test_listens_on_localhost_only` | port 27017 is listening, on loopback addresses only |
| `test_runs_as_unprivileged_user` | `mongod` runs as the `mongodb` user |
| `test_server_version` | the installed server is version 8.0.x |
| `test_answers_hello_command` | the server answers a `hello` command (sent with a minimal wire protocol client, as the release has no shell) as a writable primary |

CI runs the scenario on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/mongodb
molecule test
```
