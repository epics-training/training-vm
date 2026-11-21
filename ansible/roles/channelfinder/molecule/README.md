# Molecule tests for the channelfinder role

Functional tests: the `default` scenario builds ChannelFinder and sets it up
with Elasticsearch (role `channelfinder`, which pulls in `java`, `maven` and
`elasticsearch`) in an `ubuntu:22.04` container, then runs the testinfra
tests in `resources/tests/test_channelfinder.py`.
The container runs systemd as PID 1 (privileged, host cgroup namespace;
image definition shared in `ansible/molecule/systemd/Dockerfile.j2`), so the
role runs with `in_container: false`, exactly as on a VM, and the services
really start.

| Test | Checks |
|---|---|
| `test_service_is_running_and_enabled` | `elasticsearch` and `channelfinder` are running and enabled |
| `test_runs_as_unprivileged_user` | ChannelFinder runs as the `channelfinder` user |
| `test_configuration_is_not_world_readable` | `application.properties` (with the account passwords) is only readable by root and the service |
| `test_service_info_reports_elasticsearch_connected` | the service info (`/ChannelFinder`) reports version 5.1.0 and Elasticsearch as connected |
| `test_indices_are_created_in_elasticsearch` | the `channelfinder`, `cf_properties` and `cf_tags` indices exist |
| `test_https_connector_answers` | the HTTPS connector (port 8443, self-signed certificate) answers |
| `test_web_admin_page_is_served` | the admin web page (`/index.html`) is served |
| `test_anonymous_writes_are_refused` | creating a tag without credentials is refused (401) |
| `test_find_channels_by_name` | channels created through the REST API (as `admin`, with a property and a tag) are found by name pattern |
| `test_find_channels_by_property_value` | ... by property value |
| `test_find_channels_by_tag` | ... by tag |
| `test_channel_carries_its_property_and_tag` | a single channel is returned with its property value and tag |

Building ChannelFinder with Maven takes a few minutes.
CI runs the scenario on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/channelfinder
molecule test
```
