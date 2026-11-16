# Molecule tests for the kafka role

Functional tests: the `default` scenario installs Apache Kafka (role
`kafka`, which pulls in `java`) in an `ubuntu:22.04` container, then runs
the testinfra tests in `resources/tests/test_kafka.py`.
The container runs systemd as PID 1 (privileged, host cgroup namespace;
image definition shared in `ansible/molecule/systemd/Dockerfile.j2`), so the
role runs with `in_container: false`, exactly as on a VM, and the services
really start.

| Test | Checks |
|---|---|
| `test_service_is_running_and_enabled` | the `kafka` systemd service is running and enabled |
| `test_listens_on_localhost_only` | broker (9092) and controller (9093) ports are listening, on loopback addresses only |
| `test_runs_as_unprivileged_user` | the JVM runs as the `kafka` user |
| `test_tools_are_on_the_path` | a login shell finds `kafka-topics.sh` (`/etc/profile.d/kafka.sh`) |
| `test_produce_and_consume_a_message` | a topic can be created, a message produced and consumed again, the topic deleted |
| `test_topics_are_not_created_automatically` | `auto.create.topics.enable=false` is configured |

CI runs the scenario on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/kafka
molecule test
```
