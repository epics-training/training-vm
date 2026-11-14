# Molecule tests for the elasticsearch role

Functional tests: the `default` scenario installs Elasticsearch (role
`elasticsearch`, which pulls in `java`) in an `ubuntu:22.04` container, then runs the
testinfra tests in `resources/tests/test_elasticsearch.py`.
The container runs systemd as PID 1 (privileged, host cgroup namespace;
image definition shared in `ansible/molecule/systemd/Dockerfile.j2`), so the
role runs with `in_container: false`, exactly as on a VM, and the services
really start.

| Test | Checks |
|---|---|
| `test_service_is_running_and_enabled` | the `elasticsearch` systemd service is running and enabled |
| `test_listens_on_localhost_only` | HTTP (9200) and transport (9300) ports are listening, on loopback addresses only |
| `test_runs_as_unprivileged_user` | the JVM runs as the `elasticsearch` user |
| `test_cluster_is_usable` | `/_cluster/health` reports cluster `training-vm` as green or yellow |
| `test_security_is_disabled` | the REST API answers without credentials, version 8.x |
| `test_index_and_search_a_document` | a document can be indexed, found by a search and deleted |

CI runs the scenario on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/elasticsearch
molecule test
```
