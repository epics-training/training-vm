"""End-to-end tests: IOC with reccaster -> recceiver -> ChannelFinder."""
import json
import shlex
import time

import pytest

CF_URL = "http://localhost:8080/ChannelFinder"
EPICS_DEV_USER = "epics-dev"
RELEASE_LOCAL_PATH = "/opt/epics/RELEASE.local"
TEST_TOP = "/tmp/recsync-test"
APP = "recsyncTest"
IOC_UNIT = "molecule-recsync-ioc"
IOC_NAME = "moleculeIOC"
P = "molecule:rs:"

# With a description, an info tag, an alias, and an excluded record
TEST_DB = f"""\
record(ai, "{P}Temp") {{
  field(DESC, "Molecule temperature")
  info(archive, "monitor 1.0")
}}
record(bo, "{P}Switch") {{
  alias("{P}SwitchAlias")
}}
record(ao, "{P}Hidden") {{
}}
"""

# Build an IOC against reccaster, as a training user would
BUILD_SCRIPT = f"""\
set -e
rm -rf {TEST_TOP}
mkdir -p {TEST_TOP}
cd {TEST_TOP}
makeBaseApp.pl -t ioc {APP}
cp {RELEASE_LOCAL_PATH} configure/RELEASE.local
sed -i \\
  -e 's|^#{APP}_DBD += xxx.dbd|{APP}_DBD += reccaster.dbd|' \\
  -e 's|^#{APP}_LIBS += xxx|{APP}_LIBS += reccaster|' \\
  {APP}App/src/Makefile
make
"""


def wait_for(probe, timeout=180, interval=5):
    """Call probe() until it returns something truthy, return that."""
    deadline = time.monotonic() + timeout
    while True:
        result = probe()
        if result or time.monotonic() > deadline:
            return result
        time.sleep(interval)


def cf_get(host, path):
    result = host.run(f"curl -sS -f {shlex.quote(CF_URL + path)}")
    if not result.succeeded:
        return None
    try:
        return json.loads(result.stdout)
    except ValueError:
        return None


def ioc_channels(host):
    return cf_get(host, f"/resources/channels?~name={P}*") or []


def properties(channel):
    return {prop["name"]: prop["value"] for prop in channel["properties"]}


def channel_named(channels, name):
    return next(channel for channel in channels if channel["name"] == name)


def caster_state(host):
    """Value of the reccaster state record, as a string."""
    result = host.run(
        "bash -lc 'EPICS_CA_AUTO_ADDR_LIST=NO EPICS_CA_ADDR_LIST=localhost"
        f" caget -t {P}caster:State-Sts'"
    )
    return result.stdout.strip() if result.succeeded else None


@pytest.fixture(scope="module")
def ioc(host):
    """Build the test IOC against reccaster and run it as a systemd unit."""
    reccaster = None
    with host.sudo(EPICS_DEV_USER):
        host.run_test(f"cat > {TEST_TOP}.sh <<'EOF'\n{BUILD_SCRIPT}EOF")
        build = host.run(f"bash -l {TEST_TOP}.sh")
        assert build.succeeded, build.stdout + build.stderr

        for line in host.file(RELEASE_LOCAL_PATH).content_string.splitlines():
            if line.startswith("RECCASTER="):
                reccaster = line.partition("=")[2].strip()
        st_cmd = "\n".join(
            [
                f"dbLoadDatabase dbd/{APP}.dbd",
                f"{APP}_registerRecordDeviceDriver pdbbase",
                f'epicsEnvSet("IOCNAME", "{IOC_NAME}")',
                'epicsEnvSet("ENGINEER", "molecule")',
                # Connect right after the first announcement
                "var(reccastMaxHoldoff, 1.0)",
                'addReccasterExcludePattern("*:Hidden")',
                f"dbLoadRecords {reccaster}/db/reccaster.db"
                f' "P={P}caster:"',
                "dbLoadRecords test.db",
                "iocInit",
                "",
            ]
        )
        host.run_test(f"cat > {TEST_TOP}/st.cmd <<'EOF'\n{st_cmd}EOF")
        host.run_test(f"cat > {TEST_TOP}/test.db <<'EOF'\n{TEST_DB}EOF")

    arch = f"linux-{host.system_info.arch}"
    started = host.run(
        f"systemd-run --unit={IOC_UNIT} --uid={EPICS_DEV_USER}"
        f" --working-directory={TEST_TOP} /bin/sh -c"
        f" 'sleep infinity | bin/{arch}/{APP} st.cmd'"
    )
    assert started.succeeded, started.stderr

    yield IOC_NAME

    host.run(f"systemctl stop {IOC_UNIT}")


@pytest.fixture(scope="module")
def uploaded(host, ioc):
    """The test IOC's channels in ChannelFinder, once they are all there."""
    expected = {f"{P}Temp", f"{P}Switch", f"{P}SwitchAlias"}

    def probe():
        channels = ioc_channels(host)
        names = {channel["name"] for channel in channels}
        return channels if expected <= names else None

    channels = wait_for(probe)
    journal = host.run("journalctl -u recceiver -u " + IOC_UNIT + " -n 60")
    assert channels, (
        "IOC records never reached ChannelFinder\n" + journal.stdout
    )
    return channels


@pytest.mark.parametrize(
    "service", ["elasticsearch", "channelfinder", "recceiver"]
)
def test_service_is_running_and_enabled(host, service):
    svc = host.service(service)
    assert svc.is_running
    assert svc.is_enabled


def test_runs_as_unprivileged_user(host):
    assert host.process.filter(user="recceiver", comm="twistd")


def test_announces_on_loopback_broadcast(host):
    conf = host.file("/opt/epics-tools/services/recceiver/recceiver.conf")
    assert conf.contains("^addrlist = 127.255.255.255:5049$")
    assert conf.mode & 0o007 == 0


@pytest.mark.parametrize(
    "prop", ["recceiverID", "pvStatus", "iocName", "recordType", "archive"]
)
def test_recceiver_registered_its_properties(host, prop):
    assert cf_get(host, f"/resources/properties/{prop}")


def test_caster_finished_its_upload(host, uploaded):
    # Upload complete, connection kept alive
    assert wait_for(lambda: caster_state(host) == "Done", timeout=60)


def test_excluded_record_is_not_uploaded(host, uploaded):
    assert f"{P}Hidden" not in {channel["name"] for channel in uploaded}


def test_channel_has_ioc_and_record_properties(host, uploaded):
    props = properties(channel_named(uploaded, f"{P}Temp"))
    assert props["pvStatus"] == "Active"
    assert props["iocName"] == IOC_NAME
    assert props["recordType"] == "ai"
    assert props["recordDesc"] == "Molecule temperature"
    assert props["Engineer"] == "molecule"
    assert props["hostName"]
    assert props["recceiverID"]


def test_info_tag_becomes_a_property(host, uploaded):
    props = properties(channel_named(uploaded, f"{P}Temp"))
    assert props["archive"] == "monitor 1.0"


def test_alias_points_to_its_record(host, uploaded):
    props = properties(channel_named(uploaded, f"{P}SwitchAlias"))
    assert props["alias"] == f"{P}Switch"
    assert props["pvStatus"] == "Active"


def test_channels_are_found_by_ioc(host, uploaded):
    channels = cf_get(host, f"/resources/channels?iocName={IOC_NAME}")
    names = {channel["name"] for channel in channels}
    assert {f"{P}Temp", f"{P}Switch", f"{P}SwitchAlias"} <= names


# Keep this last: it stops the IOC
def test_stopped_ioc_channels_become_inactive(host, uploaded):
    host.run_test(f"systemctl stop {IOC_UNIT}")

    def probe():
        channels = ioc_channels(host)
        status = {properties(ch).get("pvStatus") for ch in channels}
        return channels and status == {"Inactive"}

    assert wait_for(probe), "channels of the stopped IOC are still Active"
