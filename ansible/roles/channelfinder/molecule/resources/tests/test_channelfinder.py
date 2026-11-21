"""Functional tests for the channelfinder role."""
import json
import shlex

import pytest

CF_URL = "http://localhost:8080/ChannelFinder"
CF_HTTPS_URL = "https://localhost:8443/ChannelFinder"
ES_URL = "http://127.0.0.1:9200"
ADMIN = ("admin", "adminPass")
CONFIG = "/opt/epics-tools/services/channelfinder/application.properties"

OWNER = ADMIN[0]
PROPERTY = "moleculeLocation"
TAG = "moleculeTag"
CHANNELS = {
    "molecule:cf:Temp": "Hall",
    "molecule:cf:Pressure": "Tunnel",
}


def curl(host, method, url, body=None, auth=None, insecure=False):
    """Send a request, return (HTTP status, decoded JSON reply or None)."""
    cmd = f"curl -sS -X {method} -w '\\n%{{http_code}}'"
    if insecure:
        cmd += " -k"
    if auth:
        cmd += f" -u {auth[0]}:{auth[1]}"
    if body is not None:
        cmd += " -H 'Content-Type: application/json'"
        cmd += f" -d {shlex.quote(json.dumps(body))}"
    result = host.run(f"{cmd} {shlex.quote(url)}")
    assert result.succeeded, result.stderr
    content, _, status = result.stdout.rpartition("\n")
    try:
        reply = json.loads(content)
    except ValueError:
        reply = None
    return int(status), reply


def cf(host, method, path, body=None, auth=ADMIN):
    return curl(host, method, f"{CF_URL}{path}", body, auth)


def channel_names(channels):
    return sorted(channel["name"] for channel in channels)


@pytest.fixture(scope="module")
def directory(host):
    """Create a property, a tag and channels using them; clean up after."""
    status, _ = cf(
        host, "PUT", f"/resources/properties/{PROPERTY}",
        {"name": PROPERTY, "owner": OWNER},
    )
    assert status == 200
    status, _ = cf(
        host, "PUT", f"/resources/tags/{TAG}", {"name": TAG, "owner": OWNER}
    )
    assert status == 200
    channels = [
        {
            "name": name,
            "owner": OWNER,
            "properties": [
                {"name": PROPERTY, "owner": OWNER, "value": location}
            ],
            "tags": [{"name": TAG, "owner": OWNER}],
        }
        for name, location in CHANNELS.items()
    ]
    status, _ = cf(host, "PUT", "/resources/channels", channels)
    assert status == 200

    yield CHANNELS

    for name in CHANNELS:
        cf(host, "DELETE", f"/resources/channels/{name}")
    cf(host, "DELETE", f"/resources/tags/{TAG}")
    cf(host, "DELETE", f"/resources/properties/{PROPERTY}")


@pytest.mark.parametrize("service", ["elasticsearch", "channelfinder"])
def test_service_is_running_and_enabled(host, service):
    svc = host.service(service)
    assert svc.is_running
    assert svc.is_enabled


def test_runs_as_unprivileged_user(host):
    assert host.process.filter(user="channelfinder", comm="java")


def test_configuration_is_not_world_readable(host):
    config = host.file(CONFIG)
    assert config.group == "channelfinder"
    assert config.mode & 0o007 == 0


def test_service_info_reports_elasticsearch_connected(host):
    status, info = cf(host, "GET", "", auth=None)
    assert status == 200
    assert info["version"] == "5.1.0"
    assert info["elastic"]["status"] == "Connected"


@pytest.mark.parametrize(
    "index", ["channelfinder", "cf_properties", "cf_tags"]
)
def test_indices_are_created_in_elasticsearch(host, index):
    status, _ = curl(host, "GET", f"{ES_URL}/{index}")
    assert status == 200


def test_https_connector_answers(host):
    status, info = curl(host, "GET", CF_HTTPS_URL, insecure=True)
    assert status == 200
    assert info["elastic"]["status"] == "Connected"


def test_web_admin_page_is_served(host):
    page = host.run("curl -sS -f http://localhost:8080/index.html")
    assert page.succeeded, page.stderr
    assert "ChannelFinder Admin" in page.stdout


def test_anonymous_writes_are_refused(host):
    status, _ = cf(
        host, "PUT", "/resources/tags/moleculeAnonymous",
        {"name": "moleculeAnonymous", "owner": OWNER}, auth=None,
    )
    assert status == 401


def test_find_channels_by_name(host, directory):
    status, channels = cf(
        host, "GET", "/resources/channels?~name=molecule:cf:*", auth=None
    )
    assert status == 200
    assert channel_names(channels) == sorted(directory)


def test_find_channels_by_property_value(host, directory):
    status, channels = cf(
        host, "GET", f"/resources/channels?{PROPERTY}=Hall", auth=None
    )
    assert status == 200
    assert channel_names(channels) == ["molecule:cf:Temp"]


def test_find_channels_by_tag(host, directory):
    status, channels = cf(
        host, "GET", f"/resources/channels?~tag={TAG}", auth=None
    )
    assert status == 200
    assert channel_names(channels) == sorted(directory)


def test_channel_carries_its_property_and_tag(host, directory):
    status, channel = cf(
        host, "GET", "/resources/channels/molecule:cf:Pressure", auth=None
    )
    assert status == 200
    assert {
        (prop["name"], prop["value"]) for prop in channel["properties"]
    } == {(PROPERTY, "Tunnel")}
    assert [tag["name"] for tag in channel["tags"]] == [TAG]
