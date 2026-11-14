"""Functional tests for the archiver_appliance role: Tomcat and the
Archiver Appliance are installed in the configured versions, MariaDB and
the appliance run as services, PVs served by a temporary IOC get archived
over PV Access and Channel Access, their samples land in the short term
store and can be fetched the way the Phoebus Data Browser does, and
archiving survives a restart of the appliance.

The Data Browser reads archived data over the pbraw protocol, which is an
HTTP request to <retrieval URL>/data/getData.raw. The tests take that URL
from the installed Phoebus preferences.

The tests run in file order: the ones using the archived PVs share one
temporary IOC, and the restart test has to come last.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone

import pytest
import yaml

TOMCAT_HOME = "/opt/epics-tools/lib/tomcat"
STS_FOLDER = f"{TOMCAT_HOME}/storage/sts"
PREFERENCES = "/opt/epics-tools/config/preferences.ini"
ARCHIVES_KEY = "org.csstudio.trends.databrowser3/archives="
BASE_URL = "http://localhost:17665"
MGMT_URL = f"{BASE_URL}/mgmt/bpl"
APPLIANCE_ID = "appliance0"
DB_CMD = "mariadb -u archappl --password=archappl archappl -N -e"
TEST_DIR = "/tmp/ci-aa-test"

# Test PVs, served by a temporary IOC; the appliance archives the first one
# over PV Access (its default protocol), the second one over Channel Access
TEST_PV = "ci:aa:counter"
TEST_PV_CA = "ci:aa:ca-counter"
PROTOCOLS = {TEST_PV: "pva", TEST_PV_CA: "ca"}
TEST_DB = "".join(
    f'record(calc, "{pv}") {{\n'
    '  field(SCAN, "1 second")\n'
    f'  field(INPA, "{pv}")\n'
    '  field(CALC, "A+1")\n'
    '}\n'
    for pv in PROTOCOLS
)


def wait_for(check, timeout, interval=5):
    """Call check() until it returns a truthy value or timeout expires."""
    deadline = time.monotonic() + timeout
    while True:
        result = check()
        if result or time.monotonic() > deadline:
            return result
        time.sleep(interval)


def http_get_json(host, url):
    """GET url inside the container; return the parsed JSON or None."""
    cmd = host.run("curl -sf %s", url)
    if cmd.rc != 0:
        return None
    try:
        return json.loads(cmd.stdout)
    except ValueError:
        return None


def appliance_info(host):
    url = f"{MGMT_URL}/getApplianceInfo?id={APPLIANCE_ID}"
    return http_get_json(host, url)


def pv_status(host, pv):
    status = http_get_json(host, f"{MGMT_URL}/getPVStatus?pv={pv}")
    return status[0].get("status", "") if status else ""


def databrowser_archive(host):
    """First default archive of the Data Browser, as a plain URL."""
    for line in host.file(PREFERENCES).content_string.splitlines():
        if line.startswith(ARCHIVES_KEY):
            first = line[len(ARCHIVES_KEY):].split("*")[0]
            return first.split("|")[0].replace("\\:", ":").strip()
    return ""


def retrieval_url(host):
    """The Data Browser's archive URL, as the HTTP URL pbraw requests."""
    return databrowser_archive(host).replace("pbraw://", "http://", 1)


def data_query(pv):
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    now = datetime.now(timezone.utc)
    start = (now - timedelta(minutes=10)).strftime(fmt)
    end = (now + timedelta(minutes=10)).strftime(fmt)
    return f"pv={pv}&from={start}&to={end}"


def samples(host, pv):
    """Archived samples of pv from the Data Browser's archive URL."""
    url = f"{retrieval_url(host)}/data/getData.json?{data_query(pv)}"
    data = http_get_json(host, url)
    return data[0].get("data", []) if data else []


@pytest.fixture(scope="module")
def role_defaults():
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "defaults", "main.yml"
    )
    with open(path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def test_ioc(host):
    """Run a temporary IOC serving the test PVs over Channel Access and
    PV Access."""
    host.run_expect([0], "mkdir -p %s", TEST_DIR)
    host.run_expect([0], "printf '%%s' %s > %s/test.db", TEST_DB, TEST_DIR)
    host.run_expect(
        [0],
        "bash -lc 'cd %s && setsid nohup softIocPVA -S -d test.db"
        " </dev/null >ioc.log 2>&1 & echo $! >%s/ioc.pid'",
        TEST_DIR,
        TEST_DIR,
    )
    for pv in PROTOCOLS:
        assert wait_for(
            lambda: host.run("bash -lc 'pvget -w 2 %s'", pv).rc == 0,
            timeout=30,
            interval=2,
        ), "test IOC does not serve " + pv
    yield
    host.run("kill $(cat %s/ioc.pid)", TEST_DIR)
    print(host.run("cat %s/ioc.log", TEST_DIR).stdout)


@pytest.fixture(scope="module")
def archived_pvs(host, test_ioc):
    """Have the appliance archive the test PVs, each over its protocol
    (the prefix ca:// or pva:// selects it)."""
    for pv, protocol in PROTOCOLS.items():
        host.run_expect(
            [0],
            "curl -sf %s",
            f"{MGMT_URL}/archivePV?pv={protocol}://{pv}"
            "&samplingperiod=1&samplingmethod=MONITOR",
        )
    for pv in PROTOCOLS:
        assert wait_for(
            lambda: pv_status(host, pv) == "Being archived", timeout=180
        ), pv + " not archived"


# --- Installation ---

def test_tomcat_version(host, role_defaults):
    notes = host.file(f"{TOMCAT_HOME}/RELEASE-NOTES").content_string
    assert f"Apache Tomcat Version {role_defaults['tomcat_version']}" in notes


def test_appliance_version(host, role_defaults):
    info = appliance_info(host)
    version = role_defaults["archiver_appliance_version"]
    assert info, "getApplianceInfo failed"
    assert info.get("version") == f"Archiver Appliance Version {version}"


def test_all_components_are_deployed_with_the_same_version(host):
    # getVersions asks engine, etl and retrieval for their versions
    versions = http_get_json(host, f"{MGMT_URL}/getVersions?id={APPLIANCE_ID}")
    assert versions, "getVersions failed"
    for component in ("engine", "etl", "retrieval"):
        assert versions.get(f"{component}_version") == versions["mgmt_version"]
    assert "components_with_different_versions" not in versions


def test_database_tables_exist(host):
    tables = host.check_output(f"{DB_CMD} %s", "show tables").split()
    for table in ("PVTypeInfo", "PVAliases", "ArchivePVRequests",
                  "ExternalDataServers"):
        assert table in tables


def test_databrowser_uses_local_archiver(host):
    assert databrowser_archive(host) == "pbraw://localhost:17665/retrieval"


# --- Services ---

@pytest.mark.parametrize("service", ["mariadb", "archiver-appliance"])
def test_service_is_running_and_enabled(host, service):
    svc = host.service(service)
    assert svc.is_running
    assert svc.is_enabled


def test_appliance_is_running(host):
    info = appliance_info(host)
    assert info and info.get("identity") == APPLIANCE_ID


def test_management_ui_is_served(host):
    # the page the Training-VM homepage links to
    url = f"{BASE_URL}/mgmt/ui/index.html"
    host.run_expect([0], "curl -sf -o /dev/null %s", url)


# --- Archiving ---

@pytest.mark.parametrize("pv", PROTOCOLS)
def test_pv_is_archived_over_requested_protocol(host, archived_pvs, pv):
    info = http_get_json(host, f"{MGMT_URL}/getPVTypeInfo?pv={pv}")
    assert info, "no PVTypeInfo for " + pv
    use_pva = str(info.get("usePVAccess")).lower() == "true"
    assert use_pva == (PROTOCOLS[pv] == "pva")


def test_archived_pvs_are_stored_in_database(host, archived_pvs):
    pvs = host.check_output(f"{DB_CMD} %s", "select pvName from PVTypeInfo")
    for pv in PROTOCOLS:
        assert pv in pvs.split()


@pytest.mark.parametrize("pv", PROTOCOLS)
def test_samples_are_written_to_short_term_store(host, archived_pvs, pv):
    # PV name -> path: ':' and '-' become '/', terminated by ':'
    key = pv.replace(":", "/").replace("-", "/")
    folder, name = os.path.split(f"{STS_FOLDER}/{key}")

    def pb_files():
        cmd = host.run("find %s -name %s", folder, f"{name}:*.pb")
        return cmd.stdout.split() if cmd.rc == 0 else []

    assert wait_for(pb_files, timeout=120), f"no {name}:*.pb in {folder}"


@pytest.mark.parametrize("pv", PROTOCOLS)
def test_databrowser_can_fetch_archived_samples(host, archived_pvs, pv):
    found = wait_for(lambda: len(samples(host, pv)) >= 3, timeout=120)
    assert found, f"no samples of {pv} from {retrieval_url(host)}"


def test_databrowser_can_fetch_raw_data(host, archived_pvs):
    # ...in the pbraw format the Data Browser actually requests
    raw = host.run(
        "curl -sf -o /dev/null -w '%%{size_download}' %s",
        f"{retrieval_url(host)}/data/getData.raw?{data_query(TEST_PV)}",
    )
    assert raw.rc == 0 and int(raw.stdout) > 0


def test_archiving_survives_restart(host, archived_pvs):
    # Must run last: stopping the appliance moves the short term store
    # into the medium term store (consolidateOnShutdown)
    restarted = time.time()
    host.run_expect([0], "systemctl restart archiver-appliance")
    assert wait_for(lambda: appliance_info(host), timeout=180), "no restart"

    for pv in PROTOCOLS:
        assert wait_for(
            lambda: pv_status(host, pv) == "Being archived", timeout=180
        ), pv + " not archived after restart"

        def new_samples():
            return [s for s in samples(host, pv) if s["secs"] > restarted]

        assert wait_for(new_samples, timeout=120), \
            f"no new samples of {pv} after restart"
