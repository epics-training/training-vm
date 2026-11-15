# Molecule tests for the phoebus_olog_webclient role

Functional tests of the Olog web client: the `default` scenario builds Olog
and the web client and sets up Elasticsearch, MongoDB and both services
(role `phoebus_olog_webclient`, which pulls in `phoebus_olog` → `java`,
`elasticsearch`, `mongodb`) in an `ubuntu:22.04` container, then runs the
testinfra tests in `resources/tests/test_olog_webclient.py`.
The container runs systemd as PID 1 (privileged, host cgroup namespace;
image definition shared in `ansible/molecule/systemd/Dockerfile.j2`), so the
role runs with `in_container: false`, exactly as on a VM, and the services
really start.

| Test | Checks |
|---|---|
| `test_service_is_running_and_enabled` | `elasticsearch`, `mongodb`, `olog` and `olog-webclient` are running and enabled |
| `test_runs_as_unprivileged_user` | the web server runs as the `olog-webclient` user |
| `test_serves_the_application` | port 3000 serves the built application |
| `test_single_page_routes_are_served` | client-side routes fall back to the application |
| `test_build_points_at_the_olog_service` | the build contains the Olog URL, and no leftover placeholder |
| `test_browser_can_reach_olog` | Olog allows CORS requests from the web client's origin |
| `test_login_from_the_web_client` | a login from the web client's origin gets a session cookie |

CI runs the scenario on x86_64 and aarch64 (`.github/workflows/molecule.yml`).
To run it locally (needs Docker):

```bash
cd ansible/roles/phoebus_olog_webclient
molecule test
```
