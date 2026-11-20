"""Functional tests for the Phoebus save-and-restore service (with
Elasticsearch): build a folder and a configuration through the REST API,
take a snapshot on the server side and read it back."""
import json
import time

import pytest

ES_URL = "http://127.0.0.1:9200"
SAR_URL = "http://localhost:8080/save-restore"
# Demo users of the service (auth.impl=demo)
USER = "user:userPass"
# Fixed id of the root folder of the save-and-restore tree
ROOT_NODE_ID = "44bef5de-e8e6-4014-af37-b8f6c8a939a2"

# Local PV of the service's own PV pool: has a value without needing an IOC
TEST_PV = "loc://molecule_sar_test(42)"
# Unique per run, so the tests can be re-run (molecule verify) - node names
# must be unique within their parent folder
RUN_ID = time.strftime("%Y%m%d%H%M%S")
FOLDER = f"Molecule {RUN_ID}"
CONFIGURATION = f"Molecule configuration {RUN_ID}"
SNAPSHOT = f"Molecule snapshot {RUN_ID}"


def wait_for(probe, timeout=60, interval=5):
    """Call probe() until it returns something truthy, return that."""
    deadline = time.monotonic() + timeout
    while True:
        result = probe()
        if result or time.monotonic() > deadline:
            return result
        time.sleep(interval)


def request(host, url, method="GET", body=None, auth=None):
    """Return (HTTP status, decoded JSON body or None)."""
    cmd = f"curl -sS -X {method} -w '\\n%{{http_code}}' '{url}'"
    if auth:
        cmd += f" -u '{auth}'"
    if body is not None:
        cmd += f" -H 'Content-Type: application/json' -d '{json.dumps(body)}'"
    result = host.run(cmd)
    assert result.succeeded, result.stderr
    content, _, status = result.stdout.rpartition("\n")
    try:
        data = json.loads(content)
    except ValueError:
        data = None
    return int(status), data


def get_json(host, url):
    status, data = request(host, url)
    assert status == 200, f"GET {url}: HTTP {status}"
    return data


@pytest.fixture(scope="module")
def folder(host):
    """Create a folder under the root folder."""
    status, node = request(
        host, f"{SAR_URL}/node?parentNodeId={ROOT_NODE_ID}", "PUT",
        {"name": FOLDER, "nodeType": "FOLDER"}, USER,
    )
    assert status == 200, f"HTTP {status}: {node}"
    return node


@pytest.fixture(scope="module")
def configuration(host, folder):
    """Create a configuration with the test PV in the folder."""
    status, config = request(
        host, f"{SAR_URL}/config?parentNodeId={folder['uniqueId']}", "PUT",
        {
            "configurationNode": {
                "name": CONFIGURATION,
                "nodeType": "CONFIGURATION",
                "description": "Molecule test configuration",
            },
            "configurationData": {"pvList": [{"pvName": TEST_PV}]},
        },
        USER,
    )
    assert status == 200, f"HTTP {status}: {config}"
    return config


@pytest.fixture(scope="module")
def snapshot(host, configuration):
    """Let the service read the PVs of the configuration and save a snapshot."""
    config_id = configuration["configurationNode"]["uniqueId"]
    status, snap = request(
        host,
        f"{SAR_URL}/take-snapshot/{config_id}"
        f"?name={SNAPSHOT.replace(' ', '%20')}&comment=Molecule",
        "PUT", auth=USER,
    )
    assert status == 200, f"HTTP {status}: {snap}"
    return snap


@pytest.mark.parametrize("service", ["elasticsearch", "save-and-restore"])
def test_service_is_running_and_enabled(host, service):
    svc = host.service(service)
    assert svc.is_running
    assert svc.is_enabled


def test_runs_as_unprivileged_user(host):
    pid = host.check_output("systemctl show -p MainPID --value save-and-restore")
    user = host.check_output(f"ps -o user= -p {pid}")
    assert user == "save-and-restore"


def test_epics_settings_reach_the_service(host):
    """CA and PVA take their settings from the environment (jca.use_env):
    the Java options and the EPICS_* variables of the molecule.yml host_vars
    have to be in the running service process."""
    pid = host.check_output("systemctl show -p MainPID --value save-and-restore")
    cmdline = host.file(f"/proc/{pid}/cmdline").content.split(b"\0")
    assert b"-Djca.use_env=true" in cmdline
    assert b"-DdefaultProtocol=ca" in cmdline
    environ = host.file(f"/proc/{pid}/environ").content.split(b"\0")
    assert b"EPICS_CA_AUTO_ADDR_LIST=YES" in environ
    assert b"EPICS_PVA_AUTO_ADDR_LIST=YES" in environ


def test_rest_api_reports_elasticsearch_connected(host):
    info = get_json(host, f"{SAR_URL}/")
    assert info["name"] == "service-save-and-restore"
    assert info["elastic"]["status"] == "Connected"
    assert info["rootNodeID"] == ROOT_NODE_ID


def test_phoebus_client_uses_the_service(host):
    prefs = host.file("/opt/epics-tools/config/preferences.ini")
    assert prefs.contains(
        "^org.phoebus.applications.saveandrestore.client/"
        f"jmasar.service.url={SAR_URL}$"
    )


def test_root_folder_exists(host):
    root = get_json(host, f"{SAR_URL}/root")
    assert root["uniqueId"] == ROOT_NODE_ID
    assert root["nodeType"] == "FOLDER"


def test_changes_need_authentication(host):
    status, _ = request(
        host, f"{SAR_URL}/node?parentNodeId={ROOT_NODE_ID}", "PUT",
        {"name": f"Unauthenticated {RUN_ID}", "nodeType": "FOLDER"},
    )
    assert status == 401


def test_folder_is_listed_under_root(host, folder):
    children = get_json(host, f"{SAR_URL}/node/{ROOT_NODE_ID}/children")
    assert folder["uniqueId"] in [node["uniqueId"] for node in children]
    assert folder["userName"] == "user"


def test_configuration_is_stored(host, configuration):
    config_id = configuration["configurationNode"]["uniqueId"]
    data = get_json(host, f"{SAR_URL}/config/{config_id}")
    assert [pv["pvName"] for pv in data["pvList"]] == [TEST_PV]


def test_snapshot_holds_the_pv_value(host, snapshot):
    snapshot_id = snapshot["snapshotNode"]["uniqueId"]
    data = get_json(host, f"{SAR_URL}/snapshot/{snapshot_id}")
    items = data["snapshotItems"]
    assert len(items) == 1
    assert items[0]["configPv"]["pvName"] == TEST_PV
    assert items[0]["value"]["value"] == 42


def test_snapshot_is_found_by_search(host, snapshot):
    def probe():
        result = get_json(
            host, f"{SAR_URL}/search?name=%22{SNAPSHOT.replace(' ', '%20')}%22"
        )
        return [node["uniqueId"] for node in result["nodes"]]

    assert snapshot["snapshotNode"]["uniqueId"] in wait_for(probe)


def test_data_is_stored_in_elasticsearch(host, snapshot):
    snapshot_id = snapshot["snapshotNode"]["uniqueId"]
    reply = get_json(
        host, f"{ES_URL}/saveandrestore_snapshot/_doc/{snapshot_id}"
    )
    assert reply["found"]
