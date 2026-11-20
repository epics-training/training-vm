# Molecule tests for the recceiver role

Functional tests of the whole RecSync / ChannelFinder stack: the `default`
scenario builds EPICS Base with the reccaster module and sets up
Elasticsearch, ChannelFinder and the recceiver (roles `initial_setup` +
`m_reccaster` + `recceiver`, which pulls in `channelfinder` → `java`,
`maven`, `elasticsearch`) in an `ubuntu:22.04` container, then runs the
testinfra tests in `resources/tests/test_recceiver.py`.
The container runs systemd as PID 1 (privileged, host cgroup namespace;
image definition shared in `ansible/molecule/systemd/Dockerfile.j2`), so the
roles run with `in_container: false`, exactly as on a VM, and the services
really start.

The end-to-end tests build an IOC against reccaster (as `epics-dev`, with
`makeBaseApp.pl`) and run it as a transient systemd unit. Its records are an
`ai` with a description and an `archive` info tag, a `bo` with an alias, and
a record excluded from the upload by `addReccasterExcludePattern`:

| Test | Checks |
|---|---|
| `test_service_is_running_and_enabled` | `elasticsearch`, `channelfinder` and `recceiver` are running and enabled |
| `test_runs_as_unprivileged_user` | the recceiver (`twistd`) runs as the `recceiver` user |
| `test_announces_on_loopback_broadcast` | `recceiver.conf` announces on `127.255.255.255:5049` and is not world-readable |
| `test_recceiver_registered_its_properties` | the recceiver created its properties (`recceiverID`, `pvStatus`, `iocName`, `recordType`, `archive`) in ChannelFinder |
| `test_caster_finished_its_upload` | the IOC's reccaster state record (read with `caget`) is `Done` |
| `test_excluded_record_is_not_uploaded` | the excluded record is not in ChannelFinder |
| `test_channel_has_ioc_and_record_properties` | the `ai` channel is `Active`, with `iocName`, `recordType`, `recordDesc`, `Engineer` (from the IOC's `ENGINEER`), `hostName` and `recceiverID` |
| `test_info_tag_becomes_a_property` | the `archive` info tag became an `archive` property |
| `test_alias_points_to_its_record` | the alias is a channel with an `alias` property naming its record |
| `test_channels_are_found_by_ioc` | ChannelFinder finds the IOC's channels by `iocName` |
| `test_stopped_ioc_channels_become_inactive` | after stopping the IOC, all its channels turn `Inactive` |

Building EPICS Base and ChannelFinder makes this one of the slower
scenarios. CI runs it on x86_64 and aarch64
(`.github/workflows/molecule.yml`). To run it locally (needs Docker):

```bash
cd ansible/roles/recceiver
molecule test
```
