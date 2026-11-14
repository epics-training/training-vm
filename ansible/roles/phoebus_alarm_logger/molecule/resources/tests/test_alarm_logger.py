"""Functional tests for the Phoebus alarm system: Kafka, alarm server,
Elasticsearch and alarm logger, end to end."""
import json
import time

import pytest

CONFIG = "Accelerator"
KAFKA = "localhost:9092"
ES_URL = "http://127.0.0.1:9200"
LOGGER_URL = "http://localhost:9000"
# The java role installs a single JDK (and removes older ones)
JAVA_ENV = "JAVA_HOME=$(ls -d /opt/epics-tools/lib/jvm/jdk-* | tail -n 1)"

# A PV that never connects: the alarm server raises a "Disconnected" alarm
TEST_PV = "molecule:alarm_logger_test"
ALARM_CONFIG_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<config name="{CONFIG}">
  <component name="Molecule">
    <pv name="{TEST_PV}">
      <description>Molecule test PV (never connects)</description>
      <enabled>true</enabled>
      <latching>true</latching>
    </pv>
  </component>
</config>
"""


def wait_for(probe, timeout=180, interval=5):
    """Call probe() until it returns something truthy, return that."""
    deadline = time.monotonic() + timeout
    while True:
        result = probe()
        if result or time.monotonic() > deadline:
            return result
        time.sleep(interval)


def get_json(host, url, body=None):
    cmd = f"curl -sS '{url}'"
    if body is not None:
        cmd += f" -H 'Content-Type: application/json' -d '{json.dumps(body)}'"
    result = host.run(cmd)
    if not result.succeeded:
        return None
    try:
        return json.loads(result.stdout)
    except ValueError:
        return None


def es_count(host, index_pattern, field, pattern):
    reply = get_json(
        host, f"{ES_URL}/{index_pattern}/_count?ignore_unavailable=true",
        {"query": {"wildcard": {field: pattern}}},
    )
    return reply.get("count", 0) if reply else 0


@pytest.fixture(scope="module")
def imported_config(host):
    """Import the test alarm configuration through the alarm-server CLI."""
    host.run(f"cat > /tmp/molecule_alarms.xml <<'XML'\n{ALARM_CONFIG_XML}XML")
    result = host.run(
        f"timeout 300 alarm-server -server {KAFKA} -config {CONFIG}"
        " -import /tmp/molecule_alarms.xml"
    )
    assert result.succeeded, result.stdout + result.stderr
    return TEST_PV


@pytest.mark.parametrize(
    "service", ["kafka", "elasticsearch", "alarm-server", "alarm-logger"]
)
def test_service_is_running_and_enabled(host, service):
    svc = host.service(service)
    assert svc.is_running
    assert svc.is_enabled


def test_alarm_server_created_its_topics(host):
    result = host.run(
        f"{JAVA_ENV} /opt/epics-tools/lib/kafka/bin/kafka-topics.sh"
        f" --bootstrap-server {KAFKA} --list"
    )
    assert result.succeeded, result.stderr
    topics = result.stdout.split()
    for topic in (CONFIG, f"{CONFIG}Command", f"{CONFIG}Talk"):
        assert topic in topics


def test_logger_rest_api_reports_elasticsearch_connected(host):
    info = get_json(host, f"{LOGGER_URL}/")
    assert info["name"] == "Alarm logging Service"
    assert info["elastic"]["status"] == "Connected"


def test_phoebus_client_uses_the_logger(host):
    prefs = host.file("/opt/epics-tools/config/preferences.ini")
    assert prefs.contains(
        f"^org.phoebus.applications.alarm.logging.ui/service_uri={LOGGER_URL}$"
    )


def test_exported_config_contains_imported_pv(host, imported_config):
    result = host.run(
        f"timeout 300 alarm-server -server {KAFKA} -config {CONFIG}"
        " -export /tmp/molecule_export.xml"
    )
    assert result.succeeded, result.stdout + result.stderr
    assert host.file("/tmp/molecule_export.xml").contains(imported_config)


def test_config_change_is_logged_to_elasticsearch(host, imported_config):
    pattern = f"*{imported_config}*"
    assert wait_for(
        lambda: es_count(
            host, f"{CONFIG.lower()}_alarms_config*", "config", pattern
        )
    ), "configuration message never reached Elasticsearch"


def test_alarm_is_logged_to_elasticsearch(host, imported_config):
    pattern = f"*{imported_config}*"
    assert wait_for(
        lambda: es_count(
            host, f"{CONFIG.lower()}_alarms_state*", "pv", pattern
        )
    ), "alarm (state) message never reached Elasticsearch"


def test_alarm_is_served_by_the_logger_rest_api(host, imported_config):
    def probe():
        reply = get_json(
            host, f"{LOGGER_URL}/search/alarm?pv=*{imported_config}*"
        )
        return reply if isinstance(reply, list) and reply else None

    assert wait_for(probe), "alarm logger REST API did not return the alarm"
